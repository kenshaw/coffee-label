#!/usr/bin/env python3
import sys
import usb.core
import usb.util
from PIL import Image

VENDOR_ID = 0x04F9
PRODUCT_ID = 0x20E1  # PT-D610BT

def print_pt(image_path: str):
    # 1. Connect to printer
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        sys.exit(f"Error: PT-D610BT (04f9:20e1) not found on USB.")

    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    dev.set_configuration()
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]

    # Out endpoint
    ep_out = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
    )

    # 2. Process image (Must fit 128 pins printable area for 24mm tape)
    img = Image.open(image_path).convert("L")
    # Rotate if wide landscape
    if img.width > img.height:
        img = img.transpose(Image.ROTATE_270)

    # Resize width to 128 dots (printable head width for 24mm tape)
    target_width = 128
    aspect = img.height / img.width
    target_height = int(target_width * aspect)
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    mono = img.point(lambda p: 1 if p < 128 else 0, mode="1")

    # 3. Build ESC/P-P raster stream
    data = bytearray()

    # Invalidate / initialize
    data += b"\x00" * 100               # 100 null bytes to clear buffer
    data += b"\x1b\x40"                 # ESC @: Initialize
    data += b"\x1b\x69\x61\x01"         # ESC i a 1: Switch to raster mode

    # Raster line data: 128 pins = 16 bytes per line
    raw_pixels = mono.tobytes()
    bytes_per_line = target_width // 8  # 16 bytes

    for y in range(mono.height):
        start = y * bytes_per_line
        line_data = raw_pixels[start:start + bytes_per_line]
        # Command 'G' (0x47): raster transfer -> G <len_low> <len_high> <data>
        data += b"\x47" + bytes_per_line.to_bytes(2, byteorder="little") + line_data

    # Print & Form Feed
    data += b"\x0c"                     # FF: print & feed/cut

    # 4. Send to USB endpoint
    print(f"[*] Dispatching {len(data)} bytes to PT-D610BT...")
    ep_out.write(data)
    print("[OK] Print complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python pt_print.py <image.png>")
    print_pt(sys.argv[1])
