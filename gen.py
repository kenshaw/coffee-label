#!/usr/bin/env python3
import os
from datetime import datetime
import cairosvg

# Native 360 dpi dimension target for 24mm tape (height: 256px, width: ~1024px)
TARGET_WIDTH = 1024
TARGET_HEIGHT = 256

COFFEE_DATABASE = {
    "sumatera": {
        "title": "SUMATERA MANDHELING",
        "origin": "IDN",
        "roast": "MEDIUM-DARK",
        "process": "WET-HULLED (GILING BASAH)",
        "notes": "EARTHY // DARK CHOCOLATE // CEDAR // HERBAL",
        "elev": "1,200-1,500M",
        "lot": "#SM-26A",
        "acidity": "LOW",
    },
    "kalosi": {
        "title": "KALOSI TORAJA",
        "origin": "IDN",
        "roast": "MEDIUM",
        "process": "WASHED / SEMI-WASHED",
        "notes": "SPICE // RIPE PLUM // BROWN SUGAR // SILKY",
        "elev": "1,400-1,800M",
        "lot": "#KT-88B",
        "acidity": "MED",
    },
    "brazilian": {
        "title": "BRAZILIAN SANTOS",
        "origin": "BRA",
        "roast": "MEDIUM",
        "process": "NATURAL / DRY",
        "notes": "NUTTY // MILK CHOCOLATE // TOASTED ALMOND",
        "elev": "800-1,200M",
        "lot": "#BS-04C",
        "acidity": "LOW",
    },
    "arabica": {
        "title": "ARABICA GOLD",
        "origin": "BLD",
        "roast": "MEDIUM-LIGHT",
        "process": "FULLY WASHED",
        "notes": "HONEY // JASMINE // CITRUS BLOSSOM // CRISP",
        "elev": "1,500-2,000M",
        "lot": "#AG-99X",
        "acidity": "BRIGHT",
    },
}

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" width="1024" height="256">
  <defs>
    <style>
      .bg {{ fill: #ffffff; }}
      .border {{ stroke: #000000; stroke-width: 2.5; fill: none; }}
      .line {{ stroke: #000000; stroke-width: 1.5; }}
      .badge-bg {{ fill: #000000; }}
      .badge-text {{ fill: #ffffff; font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace; font-size: 8px; font-weight: 700; letter-spacing: 0.3px; }}
      .title {{ fill: #000000; font-family: 'Arial Black', 'Impact', 'DejaVu Sans', 'Liberation Sans', sans-serif; font-size: 13px; font-weight: 900; letter-spacing: 0.8px; }}
      .spec-label {{ fill: #000000; font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace; font-size: 7.5px; font-weight: 700; }}
      .spec-val {{ fill: #000000; font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace; font-size: 7.5px; font-weight: 400; }}
      .telemetry {{ fill: #000000; font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace; font-size: 7px; font-weight: 600; letter-spacing: 0.2px; }}
    </style>
  </defs>

  <!-- Background and Inset Border -->
  <rect class="bg" width="400" height="100" />
  <rect class="border" x="2" y="2" width="396" height="96" rx="1.5" />

  <!-- ZONE 1: HEADER -->
  <rect class="badge-bg" x="6" y="6" width="76" height="16" rx="1" />
  <text class="badge-text" x="10" y="17.2">COFFEE//SPEC</text>

  <text class="title" x="88" y="18.5">{TITLE}</text>

  <rect class="badge-bg" x="340" y="6" width="54" height="16" rx="1" />
  <text class="badge-text" x="345" y="17.2">ORG: {ORIGIN}</text>

  <!-- Divider 1 -->
  <line class="line" x1="2" y1="27" x2="398" y2="27" />

  <!-- ZONE 2: SPECS -->
  <text class="spec-label" x="8" y="42">ROAST:</text>
  <text class="spec-val" x="42" y="42">{ROAST}</text>

  <text class="spec-label" x="145" y="42">PROCESS:</text>
  <text class="spec-val" x="190" y="42">{PROCESS}</text>

  <text class="spec-label" x="8" y="58">PROFILE:</text>
  <text class="spec-val" x="50" y="58">{NOTES}</text>

  <!-- Divider 2 -->
  <line class="line" x1="2" y1="69" x2="398" y2="69" />

  <!-- ZONE 3: TELEMETRY -->
  <text class="telemetry" x="8" y="85">ELEV: {ELEV}</text>
  <text class="telemetry" x="108" y="85">|</text>
  <text class="telemetry" x="118" y="85">LOT: {LOT}</text>
  <text class="telemetry" x="185" y="85">|</text>
  <text class="telemetry" x="195" y="85">ACIDITY: {ACIDITY}</text>

  <rect class="badge-bg" x="312" y="74" width="82" height="18" rx="1" />
  <text class="badge-text" x="318" y="86.2">PACK: {PACK_DATE}</text>
</svg>
"""

def generate_label(coffee_key: str, data: dict, pack_date: str = None):
    if not pack_date:
        pack_date = datetime.now().strftime("%Y.%m")

    svg_content = SVG_TEMPLATE.format(
        TITLE=data["title"],
        ORIGIN=data["origin"],
        ROAST=data["roast"],
        PROCESS=data["process"],
        NOTES=data["notes"],
        ELEV=data["elev"],
        LOT=data["lot"],
        ACIDITY=data["acidity"],
        PACK_DATE=pack_date,
    )

    out_png = f"label_{coffee_key}.png"
    cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        write_to=out_png,
        output_width=TARGET_WIDTH,
        output_height=TARGET_HEIGHT,
    )
    print(f"[OK] Rendered {out_png}")

if __name__ == "__main__":
    for key, data in COFFEE_DATABASE.items():
        generate_label(key, data)
