# Label Generators for Brother PT-D610BT

SVG label designs for **24mm Brother TZe tape**, rendered to PNG and printed
over USB from Arch Linux with `coffee/print.py` (Brother P-touch raster
protocol, no CUPS driver needed).

| Directory | Contents |
|-----------|----------|
| [`coffee/`](coffee/README.md) | Coffee bean labels, plus the printer script `print.py` and full setup notes (udev rule, kernel driver, tape and print-area details, troubleshooting) |
| [`spice/`](spice/gen.py) | Spice (rempah) labels in Bahasa Indonesia: garam, lada hitam, lada putih, kayu manis, bawang putih, bawang bombai, paprika |

## Setup

One virtual environment at the repository root serves both generators:

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -r coffee/requirements.txt
```

System packages, the USB udev rule and troubleshooting are in
[coffee/README.md](coffee/README.md).

## Spice labels

Generate all seven labels (SVG and 1024x256 PNG, written next to `gen.py`):

```bash
.venv/bin/python spice/gen.py
```

Layout: a black icon panel on the right; on the left a vertical English name,
a thin rule with a star, and the large centered Bahasa Indonesia name.
Names, English text and title sizes live in `SPICES` in `spice/gen.py`;
icons are the `ICONS` entries, and `ICON_SHIFT` / `TILT` / `FLIPPED` adjust
how each icon sits in the panel. Title fonts can be tried with
`--font {arial-black,impact,georgia,mono} --out DIR`.

## Printing

Make sure the printer is on, connected over USB and loaded with 24mm TZe tape.

Preview the exact 1-bit bitmap without printing:

```bash
.venv/bin/python coffee/print.py spice/label_garam.png --preview preview.png
```

Print a label:

```bash
.venv/bin/python coffee/print.py spice/label_garam.png
```

Print several in a row, using `--chain` on all but the last to save tape:

```bash
.venv/bin/python coffee/print.py spice/label_garam.png --chain
```

```bash
.venv/bin/python coffee/print.py spice/label_lada_hitam.png
```

Other options (`--margin`, `--threshold`, `--tape`) are listed in
[coffee/README.md](coffee/README.md#print).
