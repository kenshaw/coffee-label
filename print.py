#!/usr/bin/env python3
"""Print a label image to a Brother PT-D610BT over USB using raster mode.

The label image is read left-to-right as it should appear on the tape. Its
height is scaled to the printable pins of the loaded tape (128 pins / 18mm on
24mm tape) and its length is printed at 180 dpi with a configurable blank
margin at each end.
"""
import argparse
import sys
import time

import usb.core
import usb.util
from PIL import Image

VENDOR_ID = 0x04F9
PRODUCT_ID = 0x20E1  # PT-D610BT

HEAD_PINS = 128
BYTES_PER_LINE = HEAD_PINS // 8
DPI = 180

# Tape width (mm) -> printable pins at 180 dpi, centered on the head.
TAPE_PINS = {4: 24, 6: 32, 9: 52, 12: 76, 18: 120, 24: 128}

ERR1 = {
    0x01: "no media",
    0x04: "cutter jam",
    0x08: "weak batteries",
    0x40: "high-voltage adapter",
}
ERR2 = {
    0x01: "wrong media",
    0x10: "cover open",
    0x20: "overheating",
}

STATUS_COMPLETED = 0x01
STATUS_ERROR = 0x02


class Printer:
    def __init__(self):
        self.dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if self.dev is None:
            sys.exit("Error: PT-D610BT (04f9:20e1) not found on USB.")

        # usblp claims the printer interface; detach it and give it back later
        self.reattach = False
        try:
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
                self.reattach = True
        except usb.core.USBError as e:
            sys.exit(f"Error: cannot detach kernel driver: {e} (check device permissions)")

        self.dev.set_configuration()
        intf = self.dev.get_active_configuration()[(0, 0)]
        usb.util.claim_interface(self.dev, intf)
        self.ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        self.ep_in = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )
        if self.ep_out is None or self.ep_in is None:
            sys.exit("Error: could not locate USB endpoints.")

    def close(self):
        usb.util.dispose_resources(self.dev)
        if self.reattach:
            try:
                self.dev.attach_kernel_driver(0)
            except usb.core.USBError:
                pass

    def write(self, data: bytes):
        self.ep_out.write(data)

    def read_status(self, timeout: float = 2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                data = bytes(self.ep_in.read(32, timeout=500))
            except usb.core.USBTimeoutError:
                continue
            if len(data) == 32 and data[0] == 0x80:
                return data
        return None

    def drain(self):
        while self.read_status(timeout=0.2):
            pass

    def status(self):
        self.write(b"\x1b\x69\x53")  # ESC i S: status request
        status = self.read_status()
        if status is None:
            sys.exit("Error: printer did not answer the status request.")
        return status


def status_errors(status: bytes):
    errors = [msg for bit, msg in ERR1.items() if status[8] & bit]
    errors += [msg for bit, msg in ERR2.items() if status[9] & bit]
    return errors


def prepare(image_path: str, pins: int, threshold: int, margin_mm: float = 0.0) -> Image.Image:
    """Return a 1-bit image with one row per raster line (HEAD_PINS wide)."""
    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, "white")
        img = Image.alpha_composite(bg, img)
    img = img.convert("L")

    # Scale label height to the printable pins, keeping aspect ratio
    length = max(1, round(img.width * pins / img.height))
    if img.size != (length, pins):
        img = img.resize((length, pins), Image.Resampling.LANCZOS)

    # Ink = 1 bit. Transpose so each row is one tape column: the top of the
    # label lands on the MSB of the first byte, the left edge prints first.
    ink = img.point(lambda p: 255 if p < threshold else 0).convert("1", dither=Image.Dither.NONE)
    lines = ink.transpose(Image.Transpose.TRANSPOSE)

    # Blank lines before and after the label, along the tape length
    pad = round(margin_mm * DPI / 25.4)
    canvas = Image.new("1", (HEAD_PINS, lines.height + 2 * pad), 0)
    canvas.paste(lines, ((HEAD_PINS - pins) // 2, pad))
    return canvas


def build_job(canvas: Image.Image, tape_mm: int, chain: bool) -> bytes:
    n = canvas.height
    buf = bytearray()
    buf += b"\x1b\x69\x61\x01"                 # ESC i a: raster mode
    buf += b"\x1b\x69\x7a"                     # ESC i z: print information
    buf += bytes([0x00, 0x00, tape_mm, 0x00])
    buf += n.to_bytes(4, "little")
    buf += b"\x02\x00"
    buf += b"\x1b\x69\x64\x01\x00"             # ESC i d: 1 dot feed margin
    buf += b"\x4d\x00"                         # M: no compression
    buf += b"\x1b\x69\x4d\x40"                 # ESC i M: auto cut
    if chain:
        buf += b"\x1b\x69\x4b\x00"             # ESC i K: chain printing

    raw = canvas.tobytes()
    for y in range(n):
        line = raw[y * BYTES_PER_LINE:(y + 1) * BYTES_PER_LINE]
        buf += b"\x47" + BYTES_PER_LINE.to_bytes(2, "little") + line

    buf += b"\x1a"                             # print with feed
    return bytes(buf)


def main():
    ap = argparse.ArgumentParser(description="Print a label image to a Brother PT-D610BT.")
    ap.add_argument("image", help="label image (PNG etc.), oriented as it should read on the tape")
    ap.add_argument("--threshold", type=int, default=128,
                    help="gray level below which a pixel is printed (default: 128)")
    ap.add_argument("--margin", type=float, default=2.0,
                    help="blank space in mm before and after the label (default: 2.0)")
    ap.add_argument("--chain", action="store_true",
                    help="skip the final feed so the next label wastes less tape")
    ap.add_argument("--tape", type=int, choices=sorted(TAPE_PINS),
                    help="tape width in mm (default: detected from printer)")
    ap.add_argument("--preview", metavar="PNG",
                    help="write the exact 1-bit bitmap to PNG instead of printing")
    args = ap.parse_args()

    if args.preview:
        tape_mm = args.tape or 24
        canvas = prepare(args.image, TAPE_PINS[tape_mm], args.threshold, args.margin)
        preview = canvas.transpose(Image.Transpose.TRANSPOSE)
        Image.eval(preview.convert("L"), lambda p: 255 - p).save(args.preview)
        print(f"[OK] Wrote {args.preview} ({preview.width}x{preview.height} @ {DPI} dpi)")
        return

    pt = Printer()
    try:
        pt.drain()
        pt.write(b"\x00" * 100 + b"\x1b\x40")  # invalidate + ESC @: initialize
        status = pt.status()
        errors = status_errors(status)
        if errors:
            sys.exit(f"Error: printer reports {', '.join(errors)}.")

        tape_mm = args.tape or status[10]
        if tape_mm not in TAPE_PINS:
            sys.exit(f"Error: unsupported or missing tape (width {status[10]}mm).")
        if args.tape and args.tape != status[10]:
            print(f"[!] Warning: --tape {args.tape} but printer reports {status[10]}mm tape.")

        canvas = prepare(args.image, TAPE_PINS[tape_mm], args.threshold, args.margin)
        job = build_job(canvas, tape_mm, args.chain)
        mm = canvas.height * 25.4 / DPI
        print(f"[*] Printing {canvas.height} lines ({mm:.1f}mm) on {tape_mm}mm tape...")
        pt.write(job)

        # Over USB the printer may not report completion, so only fail on an
        # explicit error status
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = pt.read_status(timeout=1.0)
            if status is None:
                continue
            if status[18] == STATUS_ERROR:
                sys.exit(f"Error: print failed: {', '.join(status_errors(status)) or 'unknown error'}.")
            if status[18] == STATUS_COMPLETED:
                break
        print("[OK] Print job sent.")
    finally:
        pt.close()


if __name__ == "__main__":
    main()
