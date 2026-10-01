#!/usr/bin/env python3
from datetime import datetime
from xml.sax.saxutils import escape

import cairocffi as cairo
import cairosvg

# 2x the PT-D610BT native 180 dpi print area on 24mm tape (128 x 512 dots);
# print.py scales the height down to the printable pins of the loaded tape
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
        "acidity": "LOW",
    },
    "kalosi": {
        "title": "KALOSI TORAJA",
        "origin": "IDN",
        "roast": "MEDIUM",
        "process": "WASHED / SEMI-WASHED",
        "notes": "SPICE // RIPE PLUM // BROWN SUGAR // SILKY",
        "elev": "1,400-1,800M",
        "acidity": "MED",
    },
    "brazilian": {
        "title": "BRAZILIAN SANTOS",
        "origin": "BRA",
        "roast": "MEDIUM",
        "process": "NATURAL / DRY",
        "notes": "NUTTY // MILK CHOCOLATE // TOASTED ALMOND",
        "elev": "800-1,200M",
        "acidity": "LOW",
    },
    "arabica": {
        "title": "ARABICA GOLD",
        "origin": "BLD",
        "roast": "MEDIUM-LIGHT",
        "process": "FULLY WASHED",
        "notes": "HONEY // JASMINE // CITRUS BLOSSOM // CRISP",
        "elev": "1,500-2,000M",
        "acidity": "BRIGHT",
    },
}

# Label geometry in SVG user units (viewBox 400 x 100), centered on CENTER_X
VIEW_WIDTH = 400
VIEW_HEIGHT = 100
CENTER_X = VIEW_WIDTH / 2
TEXT_WIDTH = 380
# Distance of pinned badges from the label edges (matches their gap to the top border)
EDGE_INSET = 7

# cairosvg only uses the first family of a font-family list
MONO_FONT = "'JetBrains Mono', 'DejaVu Sans Mono', monospace"
# Field labels (ROAST:, ELEV:, ...) use the ExtraBold face, one step above bold
LABEL_FONT = "'JetBrains Mono ExtraBold', 'JetBrains Mono', 'DejaVu Sans Mono', monospace"
TITLE_FONT = "'Arial Black', 'Impact', 'DejaVu Sans', 'Liberation Sans', sans-serif"

TITLE_SIZE = 28
# Cap height of the title font as a fraction of its size, for vertical centering
TITLE_CAP = 0.716
SPEC_SIZE = 10.5
TELEMETRY_SIZE = 10
TITLE_SPACING = 0.8
# Badge box relative to its font size: side padding, height, top above baseline
BADGE_PAD = 0.45
BADGE_HEIGHT = 1.75
BADGE_RISE = 1.24
TELEMETRY_SPACING = 0.2

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" width="{TARGET_WIDTH}" height="{TARGET_HEIGHT}">
  <defs>
    <style>
      .bg {{{{ fill: #ffffff; }}}}
      .border {{{{ stroke: #000000; stroke-width: 2.5; fill: none; }}}}
      .line {{{{ stroke: #000000; stroke-width: 1.5; }}}}
      .title {{{{ fill: #000000; font-family: {TITLE_FONT}; font-weight: 900; letter-spacing: {TITLE_SPACING}px; }}}}
      .mono {{{{ fill: #000000; font-family: {MONO_FONT}; font-weight: 400; }}}}
      .badge-bg {{{{ fill: #000000; }}}}
      .badge-text {{{{ fill: #ffffff; font-weight: 700; }}}}
      .telemetry {{{{ font-weight: 600; letter-spacing: {TELEMETRY_SPACING}px; }}}}
      .label {{{{ font-family: {LABEL_FONT}; font-weight: 800; }}}}
    </style>
  </defs>

  <!-- Background and Inset Border -->
  <rect class="bg" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" />
  <rect class="border" x="2" y="2" width="396" height="96" rx="1.5" />

  <!-- ZONE 1: TELEMETRY -->
{{TELEMETRY}}

  <!-- Divider 1 -->
  <line class="line" x1="2" y1="29" x2="398" y2="29" />

  <!-- ZONE 2: TITLE (vertically centered on the label) -->
{{TITLE}}

  <!-- Divider 2 -->
  <line class="line" x1="2" y1="66" x2="398" y2="66" />

  <!-- ZONE 3: SPECS -->
{{SPECS}}
{{PROFILE}}
</svg>
""".format(
    VIEW_WIDTH=VIEW_WIDTH, VIEW_HEIGHT=VIEW_HEIGHT,
    TARGET_WIDTH=TARGET_WIDTH, TARGET_HEIGHT=TARGET_HEIGHT,
    TITLE_FONT=TITLE_FONT, MONO_FONT=MONO_FONT, LABEL_FONT=LABEL_FONT,
    TITLE_SPACING=TITLE_SPACING, TELEMETRY_SPACING=TELEMETRY_SPACING,
)

# Measure at the render scale: cairo hints glyph advances to device pixels
_measure = cairo.Context(cairo.ImageSurface(cairo.FORMAT_A8, 1, 1))
_measure.scale(TARGET_WIDTH / VIEW_WIDTH, TARGET_HEIGHT / VIEW_HEIGHT)


def text_width(text: str, family: str, size: float, bold: bool, spacing: float = 0.0) -> float:
    """Advance width of text, measured the same way cairosvg lays it out."""
    first = family.split(",")[0].strip("\"' ")
    weight = cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL
    _measure.select_font_face(first, cairo.FONT_SLANT_NORMAL, weight)
    _measure.set_font_size(size)
    return _measure.text_extents(text)[4] + spacing * len(text)


def _layout(segments, size, family, spacing, bold_weight):
    """Widths of (text, style) segments, the space between them and badge padding."""
    space = text_width(" ", family, size, False, spacing)
    pad = BADGE_PAD * size
    widths = []
    for t, style in segments:
        face = LABEL_FONT if style == "label" else family
        w = text_width(t, face, size, bold_weight or style is not None, spacing)
        widths.append(w + 2 * pad if style == "badge" else w)
    total = sum(widths) + space * (len(segments) - 1) if segments else 0.0
    return widths, space, pad, total


def _emit(segments, widths, x, y, size, space, pad, classes):
    out = []
    for (t, style), w in zip(segments, widths):
        if style == "badge":
            top = y - BADGE_RISE * size
            out.append(f'  <rect class="badge-bg" x="{x:.2f}" y="{top:.2f}" width="{w:.2f}" '
                       f'height="{BADGE_HEIGHT * size:.2f}" rx="1" />')
            out.append(f'  <text class="{classes} badge-text" x="{x + pad:.2f}" y="{y}" '
                       f'font-size="{size:.2f}">{escape(t)}</text>')
        elif t:
            cls = classes + (f" {style}" if style else "")
            out.append(f'  <text class="{cls}" x="{x:.2f}" y="{y}" font-size="{size:.2f}">{escape(t)}</text>')
        x += w + space
    return out


def centered_line(segments, y: float, family: str, size: float, classes: str,
                  spacing: float = 0.0, bold_weight: bool = False, cap: float = 0.0,
                  left=None, right=None) -> str:
    """Lay out (text, style) segments as one line centered on the label.

    style is None, "label" (extra bold field name) or "badge" (white bold text
    on a black box).
    Segments are separated by one space; an empty segment adds an extra space.
    left / right are single segments pinned EDGE_INSET from the label edges;
    the other segments are then centered in the space between them.
    The font size shrinks from size only if the line would not fit.
    If cap (cap height / font size) is given, y is the vertical center of the
    capitals rather than the baseline.
    Each segment is its own <text> element since cairosvg cannot center a
    <text> containing <tspan>s.
    """
    left = [left] if left else []
    right = [right] if right else []
    pinned = left or right
    avail = VIEW_WIDTH - 2 * EDGE_INSET if pinned else TEXT_WIDTH

    def fit(sz):
        lw, space, pad, ltotal = _layout(left, sz, family, spacing, bold_weight)
        rw, _, _, rtotal = _layout(right, sz, family, spacing, bold_weight)
        mw, _, _, mtotal = _layout(segments, sz, family, spacing, bold_weight)
        gaps = 2 * space * (bool(left) + bool(right))
        return (lw, ltotal), (rw, rtotal), (mw, mtotal), space, pad, ltotal + rtotal + mtotal + gaps

    (lw, ltotal), (rw, rtotal), (mw, mtotal), space, pad, total = fit(size)
    # Hinted advances change with size, so shrink until it actually fits
    while total > avail:
        size *= avail / total * 0.995
        (lw, ltotal), (rw, rtotal), (mw, mtotal), space, pad, total = fit(size)

    if cap:
        y = round(y + cap * size / 2, 2)

    x = CENTER_X - mtotal / 2
    if pinned:
        x = (EDGE_INSET + ltotal + VIEW_WIDTH - EDGE_INSET - rtotal) / 2 - mtotal / 2

    out = _emit(left, lw, EDGE_INSET, y, size, space, pad, classes)
    out += _emit(segments, mw, x, y, size, space, pad, classes)
    out += _emit(right, rw, VIEW_WIDTH - EDGE_INSET - rtotal, y, size, space, pad, classes)
    return "\n".join(out)


def build_svg(data: dict, pack_date: str) -> str:
    title = centered_line([(data["title"], None)], 47.5, TITLE_FONT, TITLE_SIZE, "title",
                          spacing=TITLE_SPACING, bold_weight=True, cap=TITLE_CAP)
    specs = centered_line(
        [("ROAST:", "label"), (data["roast"], None), ("", None), ("", None),
         ("PROCESS:", "label"), (data["process"], None)],
        78, MONO_FONT, SPEC_SIZE, "mono")
    profile = centered_line([("PROFILE:", "label"), (data["notes"], None)], 92, MONO_FONT, SPEC_SIZE, "mono")
    telemetry = centered_line(
        [("ELEV:", "label"), (data["elev"], None), ("|", None), ("ACID:", "label"), (data["acidity"], None)],
        19.4, MONO_FONT, TELEMETRY_SIZE, "mono telemetry", spacing=TELEMETRY_SPACING, bold_weight=True,
        left=("ORG: " + data["origin"], "badge"), right=("PACK: " + pack_date, "badge"))
    return SVG_TEMPLATE.format(TITLE=title, SPECS=specs, PROFILE=profile, TELEMETRY=telemetry)


def generate_label(coffee_key: str, data: dict, pack_date: str = None) -> str:
    if not pack_date:
        pack_date = datetime.now().strftime("%Y.%m")

    svg_content = build_svg(data, pack_date)

    out_png = f"label_{coffee_key}.png"
    cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        write_to=out_png,
        output_width=TARGET_WIDTH,
        output_height=TARGET_HEIGHT,
    )
    print(f"[OK] Rendered {out_png}")
    return svg_content


if __name__ == "__main__":
    svgs = [generate_label(key, data) for key, data in COFFEE_DATABASE.items()]

    # First label's SVG, kept for manual review of the layout
    with open("reference.svg", "w") as f:
        f.write(svgs[0])
    print("[OK] Wrote reference.svg")
