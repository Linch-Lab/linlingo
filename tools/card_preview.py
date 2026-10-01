"""把 FloatingCard 單獨叫起來截圖，用來肉眼檢查圓角與配色。

用法：python tools/card_preview.py [底色] [圓角] [透明度] [輸出路徑]
"""
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
import app as A  # noqa: E402
from PIL import ImageGrab  # noqa: E402


class FakeApp:
    def __init__(self, cfg):
        self.cfg = cfg
        self.target_hwnd = None

    def copy_translation(self):
        pass

    def copy_translation2(self):
        pass

    def cancel(self):
        pass

    def card_is_empty(self):
        return True


def main():
    bg = sys.argv[1] if len(sys.argv) > 1 else "#1c1c28"
    radius = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    alpha = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    out = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.environ["TEMP"], "card-preview.png")

    cfg = dict(A.DEFAULT_CONFIG)
    cfg["card_bg"] = bg
    cfg["card_radius"] = radius
    cfg["alpha"] = alpha
    cfg["card_orig_color"] = "#b8b8c8"
    cfg["card_trans_color"] = "#ffffff"

    root = tk.Tk()
    root.withdraw()
    card = A.FloatingCard(root, FakeApp(cfg))
    card.set_orig("Hello, how are you?")
    card.set_trans("你好，你好嗎？")
    card.win.deiconify()
    card.show_at(300, 300)

    def shot():
        root.update_idletasks()
        root.update()
        x, y = card.pos
        w = card.win.winfo_width()
        h = card.win.winfo_height()
        # 抓整個虛擬桌面再自己裁，避免多螢幕負座標造成 bbox 對不上
        full = ImageGrab.grab(all_screens=True)
        img = ImageGrab.grab(all_screens=True)
        print("  card %dx%d at (%d,%d)  bg=%s radius=%d alpha=%.2f"
              % (w, h, x, y, bg, radius, alpha))
        print("  virtual screen grab: %dx%d" % (full.width, full.height))
        full.save(out)
        print("  wrote full -> %s" % out)
        root.destroy()

    root.after(900, shot)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
