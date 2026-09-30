"""Generate the LinLingo logo (vector SVG).

Output
    assets/logo.svg        horizontal lockup, dark wordmark  (light backgrounds)
    assets/logo-white.svg  horizontal lockup, white wordmark (dark backgrounds)
    assets/logo-mark.svg   the mark on its own

Why fontTools
    A wordmark that relies on <text font-family="..."> renders differently on
    every machine.  Here the glyph outlines are converted to SVG paths, so the
    logo looks identical everywhere and needs no font installed.

Usage
    python tools/make_logo.py            # from the repository root
    pip install fonttools                # dependency
"""

import os
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# ---------------------------------------------------------------- palette
BLUE_TOP = "#567AFF"
BLUE_BOT = "#0B3FB0"
ARROW = "#0D47BE"
WORD_BLUE = "#1B4FD8"          # "Lin"
WORD_DARK = "#1C1C28"          # "Lingo" — same as the app card background
WORD_WHITE = "#FFFFFF"

FONT_CANDIDATES = [r"C:\Windows\Fonts\seguisb.ttf",    # Segoe UI Semibold
                   r"C:\Windows\Fonts\segoeuib.ttf",
                   r"C:\Windows\Fonts\arialbd.ttf"]

# ---------------------------------------------------------------- geometry
UNIT = 256.0                   # mark design grid
MARK_H = 44.0                  # mark height in the lockup
GAP = 11.0                     # space between mark and wordmark
FONT_SIZE = 30.0
BASELINE = 34.0                # baseline y inside the lockup box
PAD_TOP = 2.0


def mark(scale, dx, dy, gradient_id="lg"):
    """The mark (blue rounded tile + white speech bubble + double arrow)."""
    k = scale / UNIT
    return f"""  <g transform="translate({dx:.2f},{dy:.2f}) scale({k:.6f})">
    <rect x="0" y="0" width="256" height="256" rx="58" fill="url(#{gradient_id})"/>
    <rect x="42" y="46" width="172" height="116" rx="32" fill="#FFFFFF"/>
    <path d="M64 140 L62 206 L122 158 Z" fill="#FFFFFF"/>
    <polygon points="74,72 156,72 156,57 186,82 156,107 156,92 74,92" fill="{ARROW}"/>
    <polygon points="186,118 104,118 104,103 74,128 104,153 104,138 186,138" fill="{ARROW}"/>
  </g>"""


def defs(gradient_id="lg"):
    return f"""  <defs>
    <linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BLUE_TOP}"/>
      <stop offset="1" stop-color="{BLUE_BOT}"/>
    </linearGradient>
  </defs>"""


def text_path(font, glyphset, cmap, text, size, x_offset=0.0):
    """Convert `text` to an SVG path string, scaled to `size` px."""
    upem = font["head"].unitsPerEm
    scale = size / upem
    x = x_offset
    parts = []
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        width = glyphset[gname].width * scale
        if not ch.isspace():
            pen = SVGPathPen(glyphset)
            # flip the y axis: font outlines are y-up, SVG is y-down
            glyphset[gname].draw(TransformPen(pen, Transform(scale, 0, 0, -scale, x, 0)))
            d = pen.getCommands()
            if d:
                parts.append(d)
        x += width
    return " ".join(parts), x - x_offset


def build(font_path, word_color_a, word_color_b):
    font = TTFont(font_path)
    glyphset = font.getGlyphSet()
    cmap = font.getBestCmap()

    d_lin, w_lin = text_path(font, glyphset, cmap, "Lin", FONT_SIZE)
    d_lingo, w_lingo = text_path(font, glyphset, cmap, "Lingo", FONT_SIZE, x_offset=w_lin)

    text_x = MARK_H + GAP
    total_w = text_x + w_lin + w_lingo
    total_h = MARK_H + PAD_TOP * 2 + 2

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" '
           'viewBox="0 0 {0:.2f} {1:.2f}" width="{0:.2f}" height="{1:.2f}" '
           'role="img" aria-label="LinLingo">'.format(total_w, total_h)]
    svg.append(defs())
    svg.append(mark(MARK_H, 0.0, PAD_TOP))
    svg.append('  <g transform="translate({0:.2f},{1:.2f})">'.format(text_x, BASELINE))
    svg.append('    <path d="{0}" fill="{1}"/>'.format(d_lin, word_color_a))
    svg.append('    <path d="{0}" fill="{1}"/>'.format(d_lingo, word_color_b))
    svg.append('  </g>')
    svg.append('</svg>')
    return "\n".join(svg) + "\n"


def build_mark_only(font_path):
    total = MARK_H + 4
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" '
           'viewBox="0 0 {0:.2f} {0:.2f}" width="{0:.2f}" height="{0:.2f}" '
           'role="img" aria-label="LinLingo">'.format(total)]
    svg.append(defs())
    svg.append(mark(MARK_H, 2.0, 2.0))
    svg.append('</svg>')
    return "\n".join(svg) + "\n"


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(root, "assets")
    os.makedirs(assets, exist_ok=True)

    font_path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    if not font_path:
        print("  no usable font found")
        return 1
    print("  font: %s" % font_path)

    out = [("logo.svg", build(font_path, WORD_BLUE, WORD_DARK)),
           ("logo-white.svg", build(font_path, "#FFFFFF", "#D7E2FF")),
           ("logo-mark.svg", build_mark_only(font_path))]

    for name, data in out:
        p = os.path.join(assets, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
        print("  wrote %s (%d bytes)" % (p, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
