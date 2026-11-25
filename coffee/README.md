# Coffee Label Generator & Printer for Brother PT-D610BT

A minimalist, industrial/telemetry-styled coffee label system for **24mm
Brother TZe tape**, printed from Arch Linux. Labels are laid out as SVG by
`gen.py`, rendered to PNG with `cairosvg`, and sent directly over USB by
`print.py` using Brother's P-touch raster protocol (no CUPS driver needed).

---

## 1. System Packages

Install Python, the Cairo graphics library, libusb (used by `pyusb`) and the
label fonts:

```bash
yay -S --needed python cairo libusb ttf-jetbrains-mono ttf-dejavu ttf-ms-fonts
```

| Package              | Used for                                         |
|----------------------|--------------------------------------------------|
| `python`             | Python 3 interpreter, includes the `venv` module |
| `cairo`              | SVG rendering via `cairocffi` / `cairosvg`       |
| `libusb`             | USB backend for `pyusb`                          |
| `ttf-jetbrains-mono` | Monospaced spec / telemetry text                 |
| `ttf-dejavu`         | Fallback fonts                                   |
| `ttf-ms-fonts` (AUR) | *Arial Black* for the label title                |

`ttf-ms-fonts` is optional. Without it, fontconfig substitutes another bold
sans-serif font for the title. Check what will be used with:

```bash
fc-match "Arial Black:bold"
```

## 2. Python Virtual Environment

Create a virtual environment in the project directory and install the Python
dependencies into it:

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

Either activate it for the current shell (`source .venv/bin/activate`, leave
with `deactivate`) or call the interpreter directly as `.venv/bin/python`,
as the examples below do.

## 3. USB Permissions

By default only root can talk to raw USB devices. Add a udev rule that gives
the logged-in user access to the printer (`04f9:20e1`):

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="20e1", MODE="0660", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/70-brother-pt-d610bt.rules
```

```bash
sudo udevadm control --reload-rules
```

```bash
sudo udevadm trigger --subsystem-match=usb --attr-match=idVendor=04f9
```

Then unplug and replug the printer, and check the device node is accessible
(`lsusb` shows the bus/device numbers):

```bash
lsusb -d 04f9:20e1
```

```bash
getfacl /dev/bus/usb/001/010
```

The `getfacl` output should list `user:<you>:rw-`. `TAG+="uaccess"` grants
access to whoever is logged in at the local seat. On a headless machine, use
a group instead, for example `MODE="0660", GROUP="lp"`, and add yourself to
it with `sudo usermod -aG lp $USER` (then log out and back in).

### Kernel `usblp` driver / CUPS

The kernel `usblp` module binds to the printer as `/dev/usb/lp0`.
`print.py` detaches it for the duration of a print and reattaches it
afterwards, so no blacklisting is required. If CUPS has a queue for this
printer and is printing at the same moment, the job will fail with a
"resource busy" error. Wait for CUPS to finish or remove the queue.

## 4. Usage

Make sure the printer is powered on, connected over USB, and loaded with 24mm
TZe tape.

### Generate labels

Label data lives in `COFFEE_DATABASE` in `gen.py`. Edit it, then run:

```bash
.venv/bin/python gen.py
```

This writes `label_<name>.png` for every coffee (1024x256, 2x the printer's
native 180 dpi resolution) and `reference.svg`, the SVG of the first label,
for manual review in a browser or Inkscape. The pack date defaults to the
current `YYYY.MM`.

Layout, top to bottom:

```
[ORG: IDN]       ELEV: 1,200-1,500M | ACID: LOW       [PACK: 2026.10]
                       SUMATERA MANDHELING
        ROAST: MEDIUM-DARK   PROCESS: WET-HULLED (GILING BASAH)
         PROFILE: EARTHY // DARK CHOCOLATE // CEDAR // HERBAL
```

`ORG` and `PACK` are white-on-black blocks filling the top-left and
top-right corners out to the border, so they sit in the same place on every
label, with `ELEV` / `ACID` centered between them. All other lines are
centered on the label. Each line is measured with the same fonts and scale
`cairosvg` renders with, and only shrinks if it would not fit the label
width, so long coffee names get a slightly smaller title.

### Preview

Write the exact 1-bit bitmap that would be sent to the printer, without
printing:

```bash
.venv/bin/python print.py label_sumatera.png --preview preview.png
```

### Print

```bash
.venv/bin/python print.py label_sumatera.png
```

`print.py` queries the printer first and aborts on errors (no tape, cover
open, etc.). Options:

| Option            | Effect                                                         |
|-------------------|----------------------------------------------------------------|
| `--margin MM`     | Blank space before and after the label (default `2.0`)         |
| `--chain`         | Skip the final feed so the next label wastes less tape         |
| `--threshold N`   | Gray level below which a pixel prints black (default `128`)    |
| `--tape MM`       | Override the detected tape width (4, 6, 9, 12, 18, 24)         |
| `--preview PNG`   | Write the print bitmap to a PNG instead of printing            |

## 5. Print Area & Tape Notes

- The PT-D610BT has a 128-pin, 180 dpi print head. On 24mm tape all 128
  pins are used, giving an **18mm printable band**. The remaining ~3mm on
  each side of the tape width cannot be printed. This is a hardware limit.
- For prints closer to the edges of the tape width, use **18mm tape**. The
  head prints 120 pins (16.9mm) on it, leaving ~0.5mm per side. `print.py`
  detects the tape width and scales the label to fit.
- Along the tape length, the label prints at 180 dpi (the 1024px-wide PNG
  becomes 512 dots, about 72mm) plus `--margin` at each end.
- The printer leaves a fixed blank leader before the first label after a cut.
  `--chain` reduces wasted tape when printing several labels in a row.

## 6. Troubleshooting

| Symptom                                     | Fix                                                        |
|---------------------------------------------|------------------------------------------------------------|
| `PT-D610BT (04f9:20e1) not found on USB`    | Check cable and power, `lsusb -d 04f9:20e1`                |
| `Access denied` / `cannot detach kernel driver` | udev rule not applied: see section 3, then replug     |
| `Resource busy`                             | Another program (CUPS) is using the printer                |
| `printer reports no media / cover open`     | Reload the tape cassette and close the cover               |
| Text looks too thin or too heavy            | Adjust `--threshold` (higher = heavier) and check `--preview` |
