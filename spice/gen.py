#!/usr/bin/env python3
"""Spice (rempah) labels for 24mm TZe tape, in Bahasa Indonesia.

Writes label_<key>.svg and label_<key>.png (1024x256, same format as the
coffee labels, so ../coffee/print.py prints them unchanged).
Pure black on white: every shape survives the printer's 1-bit threshold.
"""
import math
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 400, 100
OUT_W, OUT_H = 1024, 256
PANEL = 72  # width of the black icon panel, flush with the border

TITLE_FONT = "'Arial Black', 'Impact', 'DejaVu Sans', sans-serif"
MONO_FONT = "'JetBrains Mono', 'DejaVu Sans Mono', monospace"

# Title font variants: scale keeps the cap height comparable to Arial Black
FONTS = {
    "arial-black": {"family": TITLE_FONT, "weight": 900, "cap": 0.716, "scale": 1.0, "spacing": 0.6},
    "impact":      {"family": "'Impact', 'DejaVu Sans Condensed', sans-serif", "weight": 400, "cap": 0.79, "scale": 0.9, "spacing": 1.0},
    "georgia":     {"family": "'Georgia', 'DejaVu Serif', serif", "weight": 700, "cap": 0.69, "scale": 1.0, "spacing": 0.6},
    "mono":        {"family": "'JetBrains Mono', 'DejaVu Sans Mono', monospace", "weight": 800, "cap": 0.73, "scale": 0.96, "spacing": 0.0},
}
FONT = FONTS["arial-black"]

# size: title font size, tuned so the longest names fit the 276-unit text area
SPICES = {
    "garam":         {"title": "GARAM",         "english": "SALT",    "size": 60},
    "lada_hitam":    {"title": "LADA HITAM",    "english": "BLACK PEPPER",       "size": 47},
    "lada_putih":    {"title": "LADA PUTIH",    "english": "WHITE PEPPER",       "size": 47},
    "kayu_manis":    {"title": "KAYU MANIS",    "english": "CINNAMON",   "size": 47},
    "bawang_putih":  {"title": "BAWANG PUTIH",  "english": "GARLIC",     "size": 47},
    "bawang_bombai": {"title": "BAWANG BOMBAI", "english": "ONION",        "size": 47},
    "paprika":       {"title": "PAPRIKA",       "english": "PAPRIKA",    "size": 49},
}

# Icons are drawn white on the black panel, in a 60x60 box centred at (0,0)
S = 'fill="none" stroke="#fff" stroke-linecap="round" stroke-linejoin="round"'
F = 'fill="#fff"'
K = 'fill="#000"'

def _corn(cx, cy, r, solid):
    if solid:
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" {F}/>'
                f'<path d="M{cx - r * .45} {cy - r * .1} q{r * .3} {-r * .45} {r * .7} {-r * .25}" '
                f'fill="none" stroke="#000" stroke-width="2" stroke-linecap="round"/>')
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" {S}/>'
            f'<path d="M{cx - r * .45} {cy - r * .1} q{r * .3} {-r * .45} {r * .7} {-r * .25}" {S} stroke-width="2"/>')

ICONS = {
    # shaker with dome cap, holes and falling grains
    "garam": (
        f'<path d="M-13 -6 h26 l4 26 q0 6 -6 6 h-22 q-6 0 -6 -6 z" {S}/>'
        f'<path d="M-11 -6 v-8 q0 -14 11 -14 q11 0 11 14 v8" {S}/>'
        f'<circle cx="-5" cy="-17" r="1.6" {F}/><circle cx="0" cy="-21" r="1.6" {F}/>'
        f'<circle cx="5" cy="-17" r="1.6" {F}/><circle cx="0" cy="-13" r="1.6" {F}/>'
        f'<path d="M-9 8 h18" {S} stroke-width="2.4"/>'
        f'<circle cx="-18" cy="26" r="1.4" {F}/><circle cx="20" cy="24" r="1.4" {F}/>'
        f'<circle cx="23" cy="30" r="1.4" {F}/><circle cx="-23" cy="21" r="1.4" {F}/>'),
    "lada_hitam": _corn(-9, 7, 12, True) + _corn(11, 9, 10, True) + _corn(2, -13, 11, True),
    "lada_putih": _corn(-9, 7, 12, False) + _corn(11, 9, 10, False) + _corn(2, -13, 11, False),
    # two quills with visible scrolls at the ends
    "kayu_manis": (
        f'<g transform="rotate(-35)">'
        f'<path d="M-24 -12 h40 v14 h-40 z" {S} transform="translate(0 -4)"/>'
        f'<ellipse cx="16" cy="-9" rx="4" ry="7" {S} stroke-width="2.4"/>'
        f'<path d="M-24 6 h40 v14 h-40 z" {S} transform="translate(0 -2)"/>'
        f'<ellipse cx="16" cy="11" rx="4" ry="7" {S} stroke-width="2.4"/>'
        f'<path d="M-16 -9 h22 M-16 11 h22" {S} stroke-width="2"/>'
        f'</g>'),
    # bulb with pointed tip, cloves and root hairs
    "garlic": (
        f'<path d="M0 -27 q4 8 12 12 q14 6 14 18 q0 14 -14 16 h-24 q-14 -2 -14 -16 q0 -12 14 -18 q8 -4 12 -12 z" {S}/>'
        f'<path d="M0 -14 q-9 10 -4 33 M0 -14 q9 10 4 33" {S} stroke-width="2.4"/>'
        f'<path d="M-6 22 l-2 5 M0 22 v6 M6 22 l2 5" {S} stroke-width="2.4"/>'),
    # round bulb, tip, longitudinal rings
    "onion": (
        f'<path d="M0 -26 q3 7 7 10 q19 6 19 21 q0 17 -26 17 q-26 0 -26 -17 q0 -15 19 -21 q4 -3 7 -10 z" {S}/>'
        f'<path d="M0 -16 q-14 12 -2 36 M0 -16 q14 12 2 36" {S} stroke-width="2.4"/>'
        f'<path d="M-5 24 l-2 4 M0 25 v5 M5 24 l2 4" {S} stroke-width="2.4"/>'),
    # bell pepper with lobes and curled stem
    "paprika": (
        f'<path d="M-10 -14 q-18 2 -18 20 q0 20 14 22 q5 1 10 -4 q5 5 10 4 q14 -2 14 -22 q0 -18 -18 -20" {S}/>'
        f'<path d="M-5 -12 q-8 12 -2 30 M5 -12 q8 12 2 30" {S} stroke-width="2.4"/>'
        f'<path d="M-10 -14 q4 -3 10 0 q6 -3 10 0" {S}/>'
        f'<path d="M0 -14 q0 -8 -3 -12 q-2 -3 3 -5 q6 -1 9 3" {S}/>'),
}
ICONS["bawang_putih"] = ICONS.pop("garlic")
ICONS["bawang_bombai"] = ICONS.pop("onion")


# icons flipped vertically; per-icon nudge (in label units) to centre each on the panel
FLIPPED = {"bawang_putih", "bawang_bombai"}
TILT = {"bawang_putih": 20, "bawang_bombai": 20}  # degrees, clockwise
ICON_SHIFT = {
    "garam": (0.7, -1.0), "lada_hitam": (0.7, 2.3), "lada_putih": (0.5, 2.3),
    "kayu_manis": (2.9, -2.9), "bawang_putih": (-0.5, 1.2), "bawang_bombai": (-1.1, 1.8),
    "paprika": (4.4, 1.4),
}


def star(cx, cy, r, ri, points, rot=0.0):
    """Flat star: alternating outer/inner radii, first point straight up."""
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points - math.pi / 2 + math.radians(rot)
        rad = r if i % 2 == 0 else ri
        pts.append(f"{cx + rad * math.cos(a):.2f},{cy + rad * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


def build_svg(idx: int, total: int, d: dict, key: str) -> str:
    dx, dy = ICON_SHIFT.get(key, (0, 0))
    flip = -1 if key in FLIPPED else 1
    tx = 19  # centre of the vertical English text
    div_x = tx + 17
    nx = div_x + 12
    px = W - 2 - PANEL  # left edge of the icon panel
    words = d["title"].split()
    sz = round(d["size"] * FONT["scale"], 1)
    cap = FONT["cap"] * sz
    pitch = cap + 0.22 * sz
    first = 50 - (pitch * (len(words) - 1) + cap) / 2 + cap
    name = "\n".join(
        f'  <text x="{(div_x + px) / 2 + 0.3:.1f}" text-anchor="middle" y="{first + i * pitch:.1f}" font-family="{FONT["family"]}" font-weight="{FONT["weight"]}" '
        f'font-size="{sz}" letter-spacing="{FONT["spacing"]}" fill="#000">{escape(w)}</text>'
        for i, w in enumerate(words))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{OUT_W}" height="{OUT_H}">
  <rect width="{W}" height="{H}" fill="#fff"/>
  <rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="3" fill="none" stroke="#000" stroke-width="2.5"/>

  <!-- icon panel -->
  <rect x="{px}" y="2" width="{PANEL}" height="{H - 4}" rx="3" fill="#000"/>
  <rect x="{px - 2}" y="2" width="6" height="{H - 4}" fill="#000"/>
  <g transform="translate({px + PANEL / 2 + dx} {50 + dy}) rotate({TILT.get(key, 0)}) scale(0.92 {flip * 0.92})" stroke-width="3">{ICONS[key]}</g>

  <!-- english name, reading bottom to top -->
  <text transform="translate({tx - 2} 50) rotate(-90)" text-anchor="middle" font-family="{MONO_FONT}" font-weight="700" font-size="10" letter-spacing="0.5" fill="#000">{escape(d["english"])}</text>

  <!-- thin solid divider with a flat star in the middle -->
  <line x1="{div_x}" y1="10" x2="{div_x}" y2="{H / 2 - 10}" stroke="#000" stroke-width="1"/>
  <line x1="{div_x}" y1="{H / 2 + 10}" x2="{div_x}" y2="{H - 10}" stroke="#000" stroke-width="1"/>
  <path d="{star(div_x, H / 2 + 0.5, 7, 3, 5, 15)}" fill="#000"/>

  <!-- bahasa indonesia name: multi-word names stack one word per line -->
{name}
</svg>
'''


def render_png(svg_path: Path, png_path: Path) -> None:
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=OUT_W, output_height=OUT_H)
    except ImportError:
        if not shutil.which("rsvg-convert"):
            raise SystemExit("need cairosvg (pip install -r requirements.txt) or rsvg-convert")
        subprocess.run(["rsvg-convert", "-w", str(OUT_W), "-h", str(OUT_H), "-o", str(png_path), str(svg_path)], check=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", choices=FONTS, default="arial-black")
    ap.add_argument("--out", help="output directory (default: this directory)")
    args = ap.parse_args()
    FONT = FONTS[args.font]
    here = Path(args.out) if args.out else Path(__file__).parent
    here.mkdir(parents=True, exist_ok=True)
    for i, (key, d) in enumerate(SPICES.items(), 1):
        svg = here / f"label_{key}.svg"
        svg.write_text(build_svg(i, len(SPICES), d, key))
        render_png(svg, here / f"label_{key}.png")
        print(f"[OK] {svg}")
