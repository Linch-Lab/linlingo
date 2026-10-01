"""Generate the LinLingo application icon.

Output
    assets/app.ico              multi-size Windows icon (16/24/32/48/64/128/256)
    assets/apple-touch-icon.png 180x180, for iOS / Safari bookmarks
    assets/og-image.png         1200x630, social sharing preview

Design
    A rounded app tile in the brand blue gradient, holding a white speech
    bubble (the floating translation card) with a bold double arrow inside
    (translate).  Everything is drawn at 8x and downsampled with LANCZOS so
    the 16 px version stays legible.

Usage
    python tools/make_icon.py            # run from the repository root
    pip install pillow numpy             # dependencies
"""

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
BLUE_TOP = (86, 122, 255)      # lighter, top-left
BLUE_BOT = (11, 63, 176)       # deeper, bottom-right
WHITE = (255, 255, 255)
ARROW = (13, 71, 190)          # arrow colour, sits on the white bubble

S = 8                          # supersample factor
N = 256                        # design grid, in "units"
C = N * S                      # canvas pixels


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ---------------------------------------------------------------- helpers
def gradient(size):
    """Diagonal linear gradient as an RGB image."""
    xs = np.linspace(0.0, 1.0, size)
    t = (xs[:, None] + xs[None, :]) / 2.0
    top = np.array(BLUE_TOP, dtype=np.float64)
    bot = np.array(BLUE_BOT, dtype=np.float64)
    arr = top[None, None, :] + (bot - top)[None, None, :] * t[:, :, None]
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def unit(v):
    return v * S


def draw_arrow(d, x0, x1, y, thick, head, color):
    """Horizontal arrow from x0 to x1 at height y (design units)."""
    direction = 1 if x1 > x0 else -1
    tip = unit(x1)
    base = tip - direction * unit(head)
    d.line([(unit(x0), unit(y)), (base + direction * unit(thick) * 0.35, unit(y))],
           fill=color, width=int(unit(thick)))
    half = unit(head) * 0.82
    d.polygon([(tip, unit(y)),
               (base, unit(y) - half),
               (base, unit(y) + half)], fill=color)


def master(small=False):
    """Full-resolution RGBA icon.

    small=True renders a simplified mark for 16/24/32 px, where the double
    arrow would turn to mush: a single, much thicker arrow inside a slightly
    larger bubble.  This is the usual trick for keeping tiny icons readable.
    """
    # tile background
    tile = gradient(C)
    mask = Image.new("L", (C, C), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, C - 1, C - 1], radius=int(unit(58)), fill=255)
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    img.paste(tile, (0, 0), mask)

    # white speech bubble (the floating card)
    bubble = Image.new("L", (C, C), 0)
    db = ImageDraw.Draw(bubble)
    if small:
        db.rounded_rectangle([unit(38), unit(40), unit(218), unit(168)],
                             radius=int(unit(34)), fill=255)
        db.polygon([(unit(62), unit(144)),
                    (unit(58), unit(208)),
                    (unit(126), unit(160))], fill=255)
    else:
        db.rounded_rectangle([unit(42), unit(46), unit(214), unit(162)],
                             radius=int(unit(32)), fill=255)
        db.polygon([(unit(64), unit(140)),
                    (unit(62), unit(206)),
                    (unit(122), unit(158))], fill=255)
    img.paste(Image.new("RGBA", (C, C), WHITE + (255,)), (0, 0), bubble)

    # arrow(s) inside the bubble
    arrows = Image.new("L", (C, C), 0)
    da = ImageDraw.Draw(arrows)
    if small:
        draw_arrow(da, 70, 192, 104, 30, 40, 255)
    else:
        draw_arrow(da, 74, 186, 82, 20, 30, 255)
        draw_arrow(da, 186, 74, 128, 20, 30, 255)
    img.paste(Image.new("RGBA", (C, C), ARROW + (255,)), (0, 0), arrows)

    return img


def downscale(img, size):
    return img.resize((size, size), Image.LANCZOS)


# Sizes at or below this use the simplified mark
SMALL_MAX = 32


# ---------------------------------------------------------------- main
def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(root, "assets")
    os.makedirs(assets, exist_ok=True)

    m = master(small=False)

    ico_path = os.path.join(assets, "app.ico")
    sizes = [16, 24, 32, 48, 64, 128, 256]

    def frame(size):
        return downscale(master(small=(size <= SMALL_MAX)), size)

    frames = [frame(s) for s in sizes]
    frames[-1].save(ico_path, format="ICO",
                    sizes=[(s, s) for s in sizes], append_images=frames[:-1])
    print("  wrote %s  sizes=%s  (simplified mark for <= %d px)"
          % (ico_path, sizes, SMALL_MAX))

    touch = os.path.join(assets, "apple-touch-icon.png")
    frame(180).save(touch, "PNG")
    print("  wrote %s (180x180)" % touch)

    preview = os.path.join(os.environ.get("TEMP", root), "linlingo-icon-preview.png")
    sheet = Image.new("RGBA", (256 + 64 + 48 + 32 + 16 + 96, 280), (245, 245, 248, 255))
    x = 16
    for s in (256, 64, 48, 32, 16):
        f = frame(s)
        sheet.paste(f, (x, 12), f)
        x += s + 16
    sheet.save(preview, "PNG")
    print("  wrote %s (review sheet)" % preview)

    # 社群分享縮圖由 tools/make_og_image.py 產生（使用正式的 logo 向量檔），
    # 這裡不再另外繪製，避免同一張圖有兩套來源。
    return 0


if __name__ == "__main__":
    sys.exit(main())
