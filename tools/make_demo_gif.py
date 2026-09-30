"""Convert a screen recording into a web-friendly demo GIF + MP4.

Usage
    python tools/make_demo_gif.py <input.mp4> [--start 15.5] [--end 32.0]
                                  [--speed 1.6] [--gif-fps 12] [--colors 64]

What it does
    1. Scans the trimmed span and works out the tight bounding box of the
       non-background pixels, so all the dead white space is cropped away
       (a screen recording usually wastes half its pixels on empty canvas).
    2. Renders the GIF with ffmpeg's two-pass palette pipeline
       (palettegen -> paletteuse), which is dramatically smaller and cleaner
       than writing frames through PIL.
    3. Also renders an H.264 MP4.  For the web, prefer the MP4: it is roughly
       five to ten times smaller than the GIF at the same quality.

Requires ffmpeg; if it is not on PATH the script falls back to the copy bundled
with the `imageio-ffmpeg` package (pip install imageio-ffmpeg).
"""

import argparse
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--start", type=float, default=15.5)
    ap.add_argument("--end", type=float, default=32.0)
    ap.add_argument("--speed", type=float, default=1.6)
    ap.add_argument("--gif-fps", type=int, default=10)
    ap.add_argument("--colors", type=int, default=64)
    ap.add_argument("--width", type=int, default=620)
    ap.add_argument("--out", default=os.path.join(HERE, "assets", "demo.gif"))
    return ap.parse_args()


def content_box(source, start, end, samples=14, white=246, pad=10):
    """Tight bounding box of everything that is not near-white."""
    cap = cv2.VideoCapture(source)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    x0, y0, x1, y1 = w, h, 0, 0
    for i in range(samples):
        t = start + (end - start) * i / max(1, samples - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = gray < white
        # ignore isolated noise
        mask = cv2.morphologyEx(mask.astype(np.uint8) * 255,
                                cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            continue
        x0, y0 = min(x0, int(xs.min())), min(y0, int(ys.min()))
        x1, y1 = max(x1, int(xs.max())), max(y1, int(ys.max()))
    cap.release()

    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(w - 1, x1 + pad)
    y1 = min(h - 1, y1 + pad)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    # even numbers keep the encoders happy
    return x0, y0, cw - (cw % 2), ch - (ch % 2), (w, h)


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    args = parse_args()
    exe = ffmpeg_exe()
    if not exe:
        print("  ffmpeg not found; pip install imageio-ffmpeg")
        return 1
    if not os.path.exists(args.source):
        print("  source not found: %s" % args.source)
        return 1
    print("  ffmpeg: %s" % exe)

    x, y, cw, ch, (sw, sh) = content_box(args.source, args.start, args.end)
    print("  source %dx%d -> crop %dx%d at (%d,%d)  [%.0f%% of the pixels]"
          % (sw, sh, cw, ch, x, y, 100.0 * cw * ch / (sw * sh)))

    ow = min(args.width, cw)
    ow -= ow % 2
    scale = "scale=%d:-2:flags=lanczos" % ow
    crop = "crop=%d:%d:%d:%d" % (cw, ch, x, y)

    # source sample rate must be output_fps * speed so the clip keeps its motion
    src_rate = max(2, int(round(args.gif_fps * args.speed)))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # ---------------- GIF ----------------
    chain = ("[0:v]%s,%s,fps=%d,setpts=PTS/%.4f,split[a][b];"
             "[a]palettegen=max_colors=%d:stats_mode=diff[p];"
             "[b][p]paletteuse=dither=bayer:bayer_scale=2:diff_mode=rectangle"
             % (crop, scale, src_rate, args.speed, args.colors))
    cmd = [exe, "-y", "-loglevel", "error",
           "-ss", str(args.start), "-to", str(args.end), "-i", args.source,
           "-filter_complex", chain, "-loop", "0", args.out]
    rc, out = run(cmd)
    if rc != 0 or not os.path.exists(args.out):
        print("  GIF failed:\n%s" % out[-800:])
        return 1
    gif = os.path.getsize(args.out)
    print("  wrote %s  (%.2f MB, %dx%d, %d colour)"
          % (args.out, gif / 1048576.0, ow, ch * ow // cw, args.colors))

    # ---------------- MP4 ----------------
    mp4 = os.path.splitext(args.out)[0] + ".mp4"
    out_fps = max(10, args.gif_fps * 2)
    chain = "%s,%s,setpts=PTS/%.4f,fps=%d,format=yuv420p" % (crop, scale, args.speed, out_fps)
    cmd = [exe, "-y", "-loglevel", "error",
           "-ss", str(args.start), "-to", str(args.end), "-i", args.source,
           "-vf", chain, "-c:v", "libx264", "-preset", "slow", "-crf", "25",
           "-movflags", "+faststart", "-an", mp4]
    rc, out = run(cmd)
    if rc != 0 or not os.path.exists(mp4):
        print("  MP4 failed:\n%s" % out[-800:])
    else:
        m = os.path.getsize(mp4)
        print("  wrote %s  (%.2f MB, h264 crf25)  [%.1fx smaller than the GIF]"
              % (mp4, m / 1048576.0, gif / max(m, 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
