"""產生社群分享縮圖（og:image）。

為什麼要另外寫一支
    原本的 og-image 是用 PIL 另外排出的「LinLingo」文字，和正式的 logo
    是兩套不同的繪製。這裡改成直接使用 assets/logo-white.svg，
    確保縮圖與網站、應用程式圖示用的是同一份品牌資產。

怎麼把 SVG 轉成點陣
    用 Edge 的 headless 模式截圖並指定透明背景，這樣拿到的是瀏覽器
    真正渲染的結果，不必另外安裝 SVG 轉檔工具。

用法
    python tools/make_og_image.py
"""

import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(HERE, "assets")

W, H = 1200, 630
BLUE_TOP = (86, 122, 255)
BLUE_BOT = (11, 63, 176)
FG = (255, 255, 255)
DIM = (214, 224, 255)
DIM2 = (168, 190, 240)


def find_edge():
    for p in (os.path.join(os.environ.get("ProgramFiles(x86)", ""),
                           r"Microsoft\Edge\Application\msedge.exe"),
              os.path.join(os.environ.get("ProgramFiles", ""),
                           r"Microsoft\Edge\Application\msedge.exe"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""),
                           r"Microsoft\Edge\Application\msedge.exe")):
        if p and os.path.exists(p):
            return p
    return shutil.which("msedge")


def render_svg(svg_name, width, out_png):
    """用 Edge headless 把 SVG 渲染成透明背景的 PNG，回傳實際內容尺寸。"""
    edge = find_edge()
    if not edge:
        return None
    # SVG 的 viewBox 比例
    src = os.path.join(ASSETS, svg_name)
    ratio = 50.0 / 171.0
    height = int(round(width * ratio)) + 20
    html = os.path.join(os.environ.get("TEMP", HERE), "_logo_render.html")
    with open(html, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            '<html><body style="margin:0;background:transparent">'
            '<img src="%s" style="width:%dpx;display:block">'
            "</body></html>" % (src.replace("\\", "/"), width))
    if os.path.exists(out_png):
        os.remove(out_png)
    subprocess.run([edge, "--headless", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000",
                    "--force-device-scale-factor=1",
                    "--screenshot=" + out_png,
                    "--window-size=%d,%d" % (width + 10, height),
                    "file:///" + html.replace("\\", "/")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not os.path.exists(out_png):
        return None
    return Image.open(out_png).convert("RGBA")


def trim(img):
    """去掉透明邊界，取得緊實的內容範圍。"""
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > 8)
    if len(xs) == 0:
        return img
    return img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def gradient():
    xs = np.linspace(0.0, 1.0, max(W, H))
    t = (xs[:, None] + xs[None, :]) / 2.0
    top = np.array(BLUE_TOP, dtype=np.float64)
    bot = np.array(BLUE_BOT, dtype=np.float64)
    arr = top[None, None, :] + (bot - top)[None, None, :] * t[:, :, None]
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    return img.crop((0, 0, W, H))


def font(name, size):
    for c in (name, "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def main():
    tmp_png = os.path.join(os.environ.get("TEMP", HERE), "_logo_white_render.png")
    logo = render_svg("logo-white.svg", 560, tmp_png)
    if logo is None:
        print("  找不到 Edge，無法渲染 SVG")
        return 1
    logo = trim(logo)
    print("  logo 渲染完成: %dx%d" % logo.size)

    img = gradient()
    d = ImageDraw.Draw(img)

    # 左上角加一點層次，避免大面積純漸層太單調
    veil = Image.new("L", (W, H), 0)
    ImageDraw.Draw(veil).ellipse([-260, -320, 900, 420], fill=26)
    img.paste(Image.new("RGB", (W, H), (255, 255, 255)), (0, 0), veil)

    # 整組內容置中。
    # 社群平台常把縮圖裁成方形（WhatsApp、LINE 等），置中才能確保
    # 裁切之後 logo 仍然完整留在畫面裡。
    lx = (W - logo.width) // 2
    ly = 140
    img.paste(logo, (lx, ly), logo)

    # 置中文字；太寬時自動縮字級，確保在方形裁切（中央 630px）下也不會被切掉
    SAFE_W = 600

    def centered(text, y, pt, fill):
        size = pt
        while size > 16:
            f = font("segoeui.ttf", size)
            if d.textlength(text, font=f) <= SAFE_W:
                break
            size -= 1
        f = font("segoeui.ttf", size)
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2.0, y), text, font=f, fill=fill)
        if size != pt:
            print("    縮字 %dpt -> %dpt（寬度 %.0fpx）" % (pt, size, w))

    y0 = ly + logo.height
    centered("Instant translation for Windows", y0 + 48, 42, DIM)
    centered("Ctrl+Alt+T  in any text box   \u2192   type   \u2192   Enter",
             y0 + 110, 30, DIM2)
    centered("MIT licensed  \u00b7  open source  \u00b7  IME friendly",
             y0 + 168, 28, (140, 166, 224))

    out = os.path.join(ASSETS, "og-image.png")
    img.save(out, "PNG", optimize=True)
    print("  wrote %s (%dx%d, %.0f KB)"
          % (out, W, H, os.path.getsize(out) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
