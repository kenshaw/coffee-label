# Coffee Label Generator & Printer for Brother PT-D610BT

A minimalist, industrial/telemetry-styled coffee label system optimized for
**24mm Brother TZe tape** printed from Linux (Arch Linux). Labels are defined
via SVG templates, dynamically rendered using `cairosvg`, and dispatched
directly over USB via Brother's ESC/P-P raster protocol.

---

## 1. System Requirements & Prerequisites

Ensure base Cairo graphics libraries, USB development packages, and required
font families are installed on your host system:

```bash
sudo pacman -S --needed cairo pkgconf ttf-jetbrains-mono ttf-dejavu
```
