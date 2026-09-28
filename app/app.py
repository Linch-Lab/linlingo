# -*- coding: utf-8 -*-
"""
即時翻譯（Windows 全域攔截式輸入）
==================================
流程：
  1. 按全域熱鍵 Ctrl+Alt+T 開啟「翻譯模式」
  2. 點擊任意應用程式的輸入框，直接打字
  3. 打字會被攔截，先進入極簡、半透明、隨文字量自動變大的浮動卡片
  4. 卡片即時顯示「原文 + 翻譯」
  5. 按 Ctrl+Enter 把翻譯結果回填進原本的輸入框（Ctrl+Shift+Enter 回填原文）
  6. Esc 取消；再按 Ctrl+Alt+T 關閉翻譯模式

純 Python 標準庫 + tkinter，無第三方套件。
"""

import ctypes
import json
import os
import queue
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, colorchooser

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
    TRAY_ERR = ""
except Exception as e:
    HAS_TRAY = False
    TRAY_ERR = str(e)

IS_WINDOWS = True
try:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    imm32 = ctypes.windll.imm32
except Exception:
    IS_WINDOWS = False
    user32 = kernel32 = imm32 = None

# ---------- 應用資訊（發版只需改這裡） ----------
APP_NAME = "PopLingo"
APP_VERSION = "1.0.0"
CONFIG_VERSION = 1

# 建立 GitHub 專案後，只需改這幾行
GITHUB_REPO = "Linch-Lab/poplingo"
UPDATE_URL = "https://raw.githubusercontent.com/{}/main/latest.json".format(GITHUB_REPO)
RELEASES_URL = "https://github.com/{}/releases/latest".format(GITHUB_REPO)

WEBSITE_URL = "https://poplingo.billlinch.com/"   # 官網
SPONSOR_URL = "https://ko-fi.com/bill_linch"      # 贊助頁

# 翻譯服務預設值：(顯示名稱, API 網址, [常見模型], 申請 / 說明網址)
# 程式送出請求時會接上 "/chat/completions"，所以這裡只填到 base 為止。
PROVIDERS = [
    ("DeepSeek", "https://api.deepseek.com",
     ["deepseek-flash", "deepseek-v4-pro"], "https://platform.deepseek.com/"),
    ("OpenAI", "https://api.openai.com/v1",
     ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
     "https://platform.openai.com/api-keys"),
    ("阿里雲通義千問", "https://dashscope.aliyuncs.com/compatible-mode/v1",
     ["qwen-plus", "qwen-turbo", "qwen-max"], "https://bailian.console.aliyun.com/"),
    ("智譜 GLM", "https://open.bigmodel.cn/api/paas/v4",
     ["glm-4-flash", "glm-4-air", "glm-4-plus"], "https://open.bigmodel.cn/"),
    ("Kimi（Moonshot）", "https://api.moonshot.cn/v1",
     ["moonshot-v1-8k", "moonshot-v1-32k"], "https://platform.moonshot.cn/"),
    ("矽基流動 SiliconFlow", "https://api.siliconflow.cn/v1",
     ["Qwen/Qwen2.5-7B-Instruct", "deepseek-ai/DeepSeek-V3"],
     "https://cloud.siliconflow.cn/"),
    ("騰訊混元", "https://api.hunyuan.cloud.tencent.com/v1",
     ["hunyuan-turbo", "hunyuan-lite"], "https://console.cloud.tencent.com/hunyuan"),
    ("火山方舟（豆包）", "https://ark.cn-beijing.volces.com/api/v3",
     ["doubao-1.5-lite-32k"], "https://console.volcengine.com/ark"),
    ("MiniMax", "https://api.minimax.chat/v1",
     ["abab6.5s-chat"], "https://platform.minimaxi.com/"),
    ("Groq", "https://api.groq.com/openai/v1",
     ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
     "https://console.groq.com/keys"),
    ("Mistral", "https://api.mistral.ai/v1",
     ["mistral-small-latest", "mistral-large-latest"], "https://console.mistral.ai/"),
    ("OpenRouter", "https://openrouter.ai/api/v1",
     ["openai/gpt-4o-mini", "google/gemini-2.0-flash-001"], "https://openrouter.ai/keys"),
    ("Ollama（本地）", "http://localhost:11434/v1",
     ["qwen2.5:7b", "qwen2.5:3b", "llama3.1:8b", "gemma3:4b"],
     "https://ollama.com/download"),
    ("LM Studio（本地）", "http://localhost:1234/v1",
     ["local-model"], "https://lmstudio.ai/"),
    ("自訂…", "", [], ""),
]
PROVIDER_NAMES = [p[0] for p in PROVIDERS]

HELP_TEXT = """使用說明
──────────
1. 點擊任意輸入框（定位文字游標）
2. 按 Ctrl+Alt+T 開啟翻譯模式
3. 卡片出現在游標旁並取得焦點
4. 在卡片輸入文字（注音等輸入法皆可），即時顯示翻譯
5. Enter 回填翻譯到輸入框；卡片清空後再按 Enter = 送出

按鍵
──────────
Ctrl+Alt+T         開啟 / 關閉翻譯模式
Ctrl+Alt+C         把焦點拉回卡片（焦點跑到別的視窗時用）
Enter              回填翻譯（卡片清空後再按 = 送出）
Ctrl+Enter         只回填、不送出
Ctrl+Shift+Enter   回填原文
Shift+Enter        換行
Esc                取消、清空卡片

卡片
──────────
• 半透明、隨內容自動縮放
• 拖曳頂端細條或譯文區可移動位置
• 點擊其他輸入框時，卡片會自動跟隨過去
• 字級與顏色可在「設定」調整，並即時預覽

系統匣圖示
──────────
• 翻譯模式開啟時點亮、關閉時反灰
• 右鍵選單：設定 / 使用說明 / 檢查更新 / 贊助 / 退出

其他
──────────
• 關閉本視窗只是隱藏，程式仍在背景執行
• 設定檔：%APPDATA%\\PopLingo\\config.json
"""

APP_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = None


def config_path():
    """設定檔位置。

    1. 可攜模式：exe 旁有 portable.flag → 用 exe 旁的 config.json
    2. 預設：%APPDATA%\\PopLingo\\config.json（更新 / 重裝不會遺失）
    3. 若 %APPDATA% 尚無設定但專案旁有舊 config.json → 自動搬移過去
    """
    global _CONFIG_PATH
    if _CONFIG_PATH:
        return _CONFIG_PATH

    if os.path.exists(os.path.join(APP_DIR, "portable.flag")):
        _CONFIG_PATH = os.path.join(APP_DIR, "config.json")
        return _CONFIG_PATH

    base = os.environ.get("APPDATA") or APP_DIR
    d = os.path.join(base, APP_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        _CONFIG_PATH = os.path.join(APP_DIR, "config.json")
        return _CONFIG_PATH

    new_path = os.path.join(d, "config.json")
    legacy = os.path.join(APP_DIR, "config.json")
    if not os.path.exists(new_path) and os.path.exists(legacy):
        try:
            shutil.copy2(legacy, new_path)  # 舊設定自動搬移
        except Exception:
            pass
    _CONFIG_PATH = new_path
    return _CONFIG_PATH


def log(msg):
    """寫入 log 檔（pythonw 模式下沒有主控台，只能寫檔）。"""
    line = time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(msg)
    try:
        with open(os.path.join(os.path.dirname(config_path()), "poplingo.log"),
                  "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        if sys.stdout:
            print(line)
    except Exception:
        pass

DEFAULT_CONFIG = {
    "endpoint": "https://api.deepseek.com",
    "api_key": "",
    "model": "deepseek-flash",
    "source_lang": "自動偵測",
    "target_lang": "英文",
    "target_lang2": "",        # 第二外語（空=停用；原文已是 target_lang 時改翻成此語言）
    "style": "學術",
    "debounce_ms": 500,
    "intercept_mode": "all",   # all=攔截所有輸入 / auto=僅輸入框 / manual=手動(點卡片打字)
    "alpha": 0.88,
    "card_orig_size": 10,      # 卡片內「輸入文字」字級
    "card_orig_color": "#b8b8c8",   # 卡片內「輸入文字」顏色
    "card_trans_size": 12,     # 卡片內「翻譯文字」字級
    "card_trans_color": "#ffffff",  # 卡片內「翻譯文字」顏色
    "toggle_vk": 0x54,         # 'T'
    "toggle_mods": 0x0003,     # ALT|CTRL => Ctrl+Alt+T
    "commit_vk": 0x0D,         # Enter
    "commit_mods": 0x0002,     # CTRL => Ctrl+Enter (回填翻譯)
    "commit_orig_mods": 0x0006,  # CTRL|SHIFT => Ctrl+Shift+Enter (回填原文)
    "cancel_vk": 0x1B,         # Esc
    "temperature": 0.3,
    "config_version": CONFIG_VERSION,
    "check_update_on_start": True,   # 啟動時檢查更新
    "focus_vk": 0x43,          # 'C' ｜ 把焦點拉回卡片的熱鍵
    "focus_mods": 0x0003,      # ALT|CTRL => Ctrl+Alt+C
    "auto_space": True,        # 回填英文等語言時自動補一個空格
}

SOURCE_LANGS = [
    "自動偵測", "中文", "繁體中文", "簡體中文", "英文", "日文", "韓文",
    "法文", "德文", "西班牙文", "俄文", "葡萄牙文", "義大利文",
    "越南文", "泰文", "印尼文", "阿拉伯文", "荷蘭文", "波蘭文", "土耳其文",
]

TARGET_LANGS = [
    "繁體中文", "簡體中文", "英文", "日文", "韓文", "法文", "德文",
    "西班牙文", "俄文", "葡萄牙文", "義大利文", "越南文", "泰文",
    "印尼文", "阿拉伯文", "荷蘭文", "波蘭文", "土耳其文",
]

STYLES = ["學術", "商務", "閒聊"]

STYLE_PROMPTS = {
    "學術": "採用學術、正式風格；若原文結尾沒有句號，視為標題，採標題式翻譯（符合標題大小寫規範）。",
    "商務": "採用商務、專業、禮貌的正式風格。",
    "閒聊": "採用口語化、自然流暢的聊天風格。",
}

# ---------- Win32 常數 ----------
VK_BACK = 0x08
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_DELETE = 0x2E
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_LMENU = 0xA4
VK_RMENU = 0xA5

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_HOTKEY = 0x0312

KEYEVENTF_KEYUP = 0x0002
GA_ROOT = 2
CF_UNICODETEXT = 13
INJECT_MARKER = 0x0D5E0D5E  # 自己注入按鍵的標記，掛鉤看到就放行
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010

EDIT_CLASSES = {
    "Edit", "RichEdit", "RichEdit20A", "RichEdit20W", "RICHEDIT50W", "RICHEDIT60W",
    "Scintilla", "TEdit", "TMemo", "TAdvEdit", "ATL:Edit", "ThunderRT6TextBox",
}
EDIT_PREFIXES = ("WindowsForms10.EDIT", "WindowsForms10.RichEdit", "Tcx", "Chrome_RenderWidgetHostHWND")


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", RECT),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


def _setup_signatures():
    if not IS_WINDOWS:
        return
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    user32.GetKeyboardState.restype = wintypes.BOOL
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = ctypes.c_void_p
    user32.MapVirtualKeyExW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
    user32.MapVirtualKeyExW.restype = ctypes.c_uint
    user32.ToUnicodeEx.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte),
                                   wintypes.LPWSTR, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p]
    user32.ToUnicodeEx.restype = ctypes.c_int
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.SetFocus.restype = wintypes.HWND
    user32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, wintypes.DWORD, ctypes.c_size_t]
    user32.keybd_event.restype = None
    imm32.ImmGetContext.argtypes = [wintypes.HWND]
    imm32.ImmGetContext.restype = ctypes.c_void_p
    imm32.ImmGetOpenStatus.argtypes = [ctypes.c_void_p]
    imm32.ImmGetOpenStatus.restype = wintypes.BOOL
    imm32.ImmReleaseContext.argtypes = [wintypes.HWND, ctypes.c_void_p]
    imm32.ImmReleaseContext.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                                   ctypes.c_uint, ctypes.c_uint]
    user32.GetMessageW.restype = ctypes.c_int
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallNextHookEx.restype = ctypes.c_ssize_t
    user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p


_setup_signatures()


# ---------- 設定 ----------
def migrate_config(cfg):
    """舊版設定升級：日後改格式時在這裡補遷移邏輯。"""
    v = int(cfg.get("config_version", 1) or 1)
    # if v < 2:
    #     cfg.setdefault("新欄位", 預設值)
    #     v = 2
    cfg["config_version"] = max(v, CONFIG_VERSION)
    return cfg


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    path = config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return migrate_config(cfg)


def save_config(cfg):
    try:
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("設定", "無法儲存設定：{}".format(e))


def ver_tuple(s):
    """把 'v1.2.3' / '1.2.3' 轉成可比較的 tuple。"""
    parts = []
    for x in str(s).split("."):
        x = "".join(ch for ch in x if ch.isdigit())
        parts.append(int(x) if x else 0)
    return tuple(parts) or (0,)


def is_newer(latest, current):
    return ver_tuple(latest) > ver_tuple(current)


def make_tray_image(lit):
    """產生系統匣圖示：lit=True 亮藍，False 反灰。"""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (61, 90, 254, 255) if lit else (150, 150, 150, 255)
    d.ellipse([4, 4, 28, 28], fill=color)
    return img


# ---------- Win32 輔助 ----------
def get_focus_hwnd():
    if not IS_WINDOWS:
        return None
    fg = user32.GetForegroundWindow()
    if not fg:
        return None
    pid = wintypes.DWORD()
    tid = user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
    gti = GUITHREADINFO()
    gti.cbSize = ctypes.sizeof(GUITHREADINFO)
    if user32.GetGUIThreadInfo(tid, ctypes.byref(gti)):
        return gti.hwndFocus
    return None


def get_class_name(hwnd):
    if not hwnd or not IS_WINDOWS:
        return ""
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def is_editable_hwnd(hwnd):
    cls = get_class_name(hwnd)
    if not cls:
        return False
    if cls in EDIT_CLASSES:
        return True
    return cls.startswith(EDIT_PREFIXES)


def get_window_rect(hwnd):
    r = RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return r.left, r.top, r.right, r.bottom
    return None


def get_cursor_pos():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def get_caret_rect():
    """回傳目前前景視窗的文字輸入游標（caret）矩形；找不到回傳 None。"""
    if not IS_WINDOWS:
        return None
    fg = user32.GetForegroundWindow()
    if not fg:
        return None
    pid = wintypes.DWORD()
    tid = user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
    gti = GUITHREADINFO()
    gti.cbSize = ctypes.sizeof(GUITHREADINFO)
    if user32.GetGUIThreadInfo(tid, ctypes.byref(gti)):
        r = gti.rcCaret
        if r.left or r.top or r.right or r.bottom:
            return (r.left, r.top, r.right, r.bottom)
    return None


def ime_is_open():
    """檢查目前焦點視窗的 IME 是否開啟（中文模式）。"""
    if not IS_WINDOWS:
        return False
    try:
        hwnd = get_focus_hwnd()
        if not hwnd:
            return False
        hIMC = imm32.ImmGetContext(hwnd)
        if not hIMC:
            return False
        opened = bool(imm32.ImmGetOpenStatus(hIMC))
        imm32.ImmReleaseContext(hwnd, hIMC)
        return opened
    except Exception:
        return False


def virtual_screen_rect():
    """虛擬桌面範圍（含多螢幕），回傳 (x, y, w, h)。"""
    x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
    y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
    w = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
    h = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
    return x, y, w, h


def enable_dpi_awareness():
    """設為每螢幕 DPI 感知，讓座標是實際像素（多螢幕不同解析度/縮放才不會偏移）。"""
    if not IS_WINDOWS:
        return
    try:
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 == (HANDLE)-4
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        return
    except Exception:
        pass
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def tk_pos(x, y):
    """Tk geometry 位置字串（僅非 Windows 備援用）。"""
    xs = "+{}".format(int(x)) if x >= 0 else "{}".format(int(x))
    ys = "+{}".format(int(y)) if y >= 0 else "{}".format(int(y))
    return xs + ys


def move_window(hwnd, x, y):
    """用 Win32 絕對座標移動視窗。

    Tk 的 geometry 字串把負數解讀成「距右/下緣」，無法表示負的絕對座標，
    所以多螢幕（左側/上方）的位置一律用 SetWindowPos 設定。
    """
    if not hwnd or not IS_WINDOWS:
        return
    top = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
    user32.SetWindowPos(top, None, int(x), int(y), 0, 0,
                        SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)


def set_clipboard_text(text):
    if not IS_WINDOWS:
        return
    data = text.encode("utf-16-le") + b"\x00\x00"
    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    h = kernel32.GlobalAlloc(0x0002, len(data))  # GMEM_MOVEABLE
    if h:
        p = kernel32.GlobalLock(h)
        if p:
            ctypes.memmove(p, data, len(data))
            kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_UNICODETEXT, h)
    user32.CloseClipboard()


def paste_into(hwnd):
    """把剪貼簿內容貼進指定視窗（先聚焦它再送 Ctrl+V）。"""
    if not hwnd or not IS_WINDOWS:
        return
    top = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
    # 用 Alt 抖一下解除前景鎖，再聚焦目標
    inject_key(VK_MENU)
    inject_key(VK_MENU, KEYEVENTF_KEYUP)
    user32.SetForegroundWindow(top)
    time.sleep(0.03)
    user32.SetFocus(hwnd)
    time.sleep(0.03)
    inject_key(VK_CONTROL)
    inject_key(ord('V'))
    inject_key(ord('V'), KEYEVENTF_KEYUP)
    inject_key(VK_CONTROL, KEYEVENTF_KEYUP)


def vk_to_char(vk, scan_code, flags):
    """把虛擬鍵轉成目前鍵盤配置下的字元（處理 Shift / CapsLock / 擴充鍵）。"""
    if not IS_WINDOWS:
        return None
    key_state = (ctypes.c_ubyte * 256)()
    if not user32.GetKeyboardState(key_state):
        return None
    hkl = user32.GetKeyboardLayout(0)
    sc = user32.MapVirtualKeyExW(vk, 0, hkl)
    buf = (ctypes.c_wchar * 8)()
    ret = user32.ToUnicodeEx(vk, sc, key_state, buf, 8, 0, hkl)
    if ret == 1:
        return buf[0]
    if ret > 1:
        return "".join(buf[i] for i in range(ret))
    return None


def inject_key(vk, flags=0):
    """注入一個帶標記的按鍵，讓低階掛鉤放行（避免攔到自己送出的鍵）。"""
    user32.keybd_event(vk, 0, flags, INJECT_MARKER)


# ---------- 鍵盤掛鉤 ----------
class KeyboardHook:
    """WH_KEYBOARD_LL 低階鍵盤掛鉤：攔截輸入 + 偵測熱鍵組合。"""

    def __init__(self, app):
        self.app = app
        self.hook = None
        self._down = set()
        self._proc = None
        self._running = False
        self._thread = None
        self._toggle_ok = False
        self._focus_ok = False
        self.toggle_id = 0x0001
        self.focus_id = 0x0002

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        def proc(nCode, wParam, lParam):
            if nCode >= 0:
                kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if kb.dwExtraInfo == INJECT_MARKER:
                    # 自己注入的按鍵，直接放行
                    return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)
                vk = kb.vkCode
                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    self._down.add(vk)
                    if self._handle_down(vk, kb):
                        return 1
                elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                    self._down.discard(vk)
            return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

        self._proc = HOOKPROC(proc)

        # 用 RegisterHotKey 註冊熱鍵，比手動偵測修飾鍵更可靠
        tvk = int(self.app.cfg.get("toggle_vk", 0x54))
        tmods = int(self.app.cfg.get("toggle_mods", MOD_ALT | MOD_CONTROL))
        self._toggle_ok = bool(user32.RegisterHotKey(None, self.toggle_id, tmods, tvk))
        # 第二組熱鍵：把焦點拉回卡片
        fvk = int(self.app.cfg.get("focus_vk", 0x43))          # 'C'
        fmods = int(self.app.cfg.get("focus_mods", MOD_ALT | MOD_CONTROL))
        self._focus_ok = bool(user32.RegisterHotKey(None, self.focus_id, fmods, fvk))

        self.hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._proc, kernel32.GetModuleHandleW(None), 0)
        if not self.hook:
            self.app.events.put(("error_hook",))
            return
        msg = wintypes.MSG()
        while self._running:
            r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r <= 0:
                break
            if msg.message == WM_HOTKEY:
                if msg.wParam == self.toggle_id:
                    self.app.events.put(("toggle",))
                    continue
                if msg.wParam == self.focus_id:
                    self.app.events.put(("focus_card",))
                    continue
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnhookWindowsHookEx(self.hook)
        user32.UnregisterHotKey(None, self.toggle_id)
        user32.UnregisterHotKey(None, self.focus_id)

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            try:
                user32.PostThreadMessageW(self._thread.ident, 0x0012, 0, 0)
            except Exception:
                pass

    def _mod_state(self):
        d = self._down
        ctrl = (VK_CONTROL in d) or (VK_LCONTROL in d) or (VK_RCONTROL in d)
        shift = (VK_SHIFT in d) or (VK_LSHIFT in d) or (VK_RSHIFT in d)
        alt = (VK_MENU in d) or (VK_LMENU in d) or (VK_RMENU in d)
        win = (VK_LWIN in d) or (VK_RWIN in d)
        return ctrl, shift, alt, win

    def _mods_match(self, ctrl, shift, alt, win):
        m = 0
        if alt:
            m |= MOD_ALT
        if ctrl:
            m |= MOD_CONTROL
        if shift:
            m |= MOD_SHIFT
        if win:
            m |= MOD_WIN
        return m == int(self.app.cfg.get("toggle_mods", MOD_ALT | MOD_CONTROL))

    def _handle_down(self, vk, kb):
        app = self.app
        ctrl, shift, alt, win = self._mod_state()

        # 若 RegisterHotKey 註冊失敗，退回手動偵測切換熱鍵
        if not self._toggle_ok:
            if vk == int(app.cfg.get("toggle_vk", 0x54)) and self._mods_match(ctrl, shift, alt, win):
                app.events.put(("toggle",))
                return True
        return False


# ---------- 翻譯 ----------
def call_translate(text, source, target, cfg):
    style = cfg.get("style", "學術")
    style_hint = STYLE_PROMPTS.get(style, "")
    system_msg = "你是專業翻譯引擎。只輸出翻譯結果本身，不要任何說明、註解或前後文。" + style_hint
    target2 = (cfg.get("target_lang2") or "").strip()
    if target2:
        # 原文若已是目標語言，改翻成第二語言。
        # 明確列出規則，避免短句（例如兩三個中文字）被誤判為「已經是目標語言」。
        user_msg = (
            "將以下文字翻譯成{0}。\n"
            "規則：\n"
            "1. 只有當原文的主要語言「確實已經是{0}」時，才改翻譯成{1}。\n"
            "2. 若原文是中文、日文、韓文或其他任何語言，一律翻譯成{0}。\n"
            "3. 原文長度很短（例如只有兩三個字）時，不代表它已經是{0}。\n"
            "只輸出翻譯結果：\n\n{2}"
        ).format(target, target2, text)
    elif source and source != "自動偵測":
        user_msg = "把以下{}文字翻譯成{}：\n\n{}".format(source, target, text)
    else:
        user_msg = "把以下文字翻譯成{}：\n\n{}".format(target, text)

    payload = {
        "model": cfg.get("model", "deepseek-flash"),
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": cfg.get("temperature", 0.3),
        "stream": False,
    }
    endpoint = cfg.get("endpoint", "https://api.deepseek.com")
    if "deepseek.com" in endpoint:
        # 翻譯不需要思考模式；關掉可大幅降低延遲（服務不支援時會自動重試）
        payload["thinking"] = {"type": "disabled"}

    url = endpoint.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + (cfg.get("api_key") or ""),
    }

    def _post(body):
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        try:
            data = _post(payload)
        except urllib.error.HTTPError as e:
            if e.code == 400 and "thinking" in payload:
                payload.pop("thinking", None)   # 不支援此參數 → 移除後重試
                data = _post(payload)
            else:
                raise
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")
            detail = json.loads(body).get("error", {}).get("message", body[:200])
        except Exception:
            detail = body if body else str(e)
        raise RuntimeError("API 錯誤 {}：{}".format(e.code, detail))
    except urllib.error.URLError as e:
        raise RuntimeError("網路錯誤：{}（請確認 endpoint 與網路連線）".format(e.reason))
    except Exception as e:
        raise RuntimeError("連線失敗：{}".format(e))

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("回應格式異常：" + json.dumps(data, ensure_ascii=False)[:300])


# ---------- 浮動卡片 ----------
CARD_BG = "#1c1c28"
CARD_FG_ORIG = "#b8b8c8"
CARD_FG_TRANS = "#ffffff"
CARD_ACCENT = "#3d5afe"


class FloatingCard:
    """極簡、半透明、隨文字量自動變大的浮動卡片。"""

    def __init__(self, root, app):
        self.app = app
        cfg = app.cfg
        self.pos = (0, 0)
        self.orig_size = int(cfg.get("card_orig_size", 10))
        self.orig_color = cfg.get("card_orig_color", "#b8b8c8")
        self.trans_size = int(cfg.get("card_trans_size", 12))
        self.trans_color = cfg.get("card_trans_color", "#ffffff")

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", float(cfg.get("alpha", 0.88)))
        except Exception:
            pass

        outer = tk.Frame(self.win, bg="#3a3a48")
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=CARD_BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # 頂部拖曳條（無任何文字），用來移動卡片
        dragbar = tk.Frame(inner, bg=CARD_BG, height=7, cursor="fleur")
        dragbar.pack(fill="x", side="top")
        dragbar.pack_propagate(False)
        dragbar.bind("<ButtonPress-1>", self._start_drag)
        dragbar.bind("<B1-Motion>", self._on_drag)

        self.orig = tk.Text(inner, bg=CARD_BG, fg=self.orig_color, insertbackground=self.trans_color,
                            relief="flat", borderwidth=0, highlightthickness=0, wrap="word",
                            font=("Microsoft YaHei UI", self.orig_size), padx=6, pady=0, cursor="arrow")
        self.orig.pack(fill="x", side="top")
        self.orig.bind("<<Modified>>", self._on_modified)
        self.orig.bind("<Button-1>", self._focus_orig)

        self.trans = tk.Label(inner, text="", bg=CARD_BG, fg=self.trans_color,
                              justify="left", anchor="nw", wraplength=420,
                              font=("Microsoft YaHei UI", self.trans_size, "bold"))
        self.trans.pack(fill="x", side="top", padx=6, pady=(2, 2))
        self.trans.bind("<Double-Button-1>", lambda e: self.app.copy_translation())
        self.trans.bind("<ButtonPress-1>", self._start_drag)
        self.trans.bind("<B1-Motion>", self._on_drag)

        self.trans2 = tk.Label(inner, text="", bg=CARD_BG, fg=self.trans_color,
                               justify="left", anchor="nw", wraplength=420,
                               font=("Microsoft YaHei UI", self.trans_size, "bold"))
        self.trans2.bind("<Double-Button-1>", lambda e: self.app.copy_translation2())
        self.trans2.bind("<ButtonPress-1>", self._start_drag)
        self.trans2.bind("<B1-Motion>", self._on_drag)

        # 熱鍵綁定（焦點在卡片時也可用）
        self.win.bind("<Escape>", lambda e: self.app.cancel())
        self.orig.bind("<Return>", self._on_enter)
        self.orig.bind("<Shift-Return>", self._on_shift_enter)
        self.orig.bind("<BackSpace>", self._on_backspace)
        self.orig.bind("<Control-Return>", self._on_ctrl_enter)
        self.orig.bind("<Control-Shift-Return>", self._on_ctrl_shift_enter)

        self.win.withdraw()

    @property
    def hwnd(self):
        return self.win.winfo_id() if IS_WINDOWS else 0

    def focus(self):
        try:
            self.win.focus_force()
            self.orig.focus_set()
        except Exception:
            pass

    def _focus_orig(self, event=None):
        # 記住點進卡片前聚焦的視窗，作為回填目標（手動模式用）
        hwnd = get_focus_hwnd()
        if hwnd and not self.app.is_focus_our_window():
            self.app.target_hwnd = hwnd
        self.focus()

    def _start_drag(self, e):
        self._drag_off = (e.x_root - self.pos[0], e.y_root - self.pos[1])

    def _on_drag(self, e):
        self.move_to(e.x_root - self._drag_off[0], e.y_root - self._drag_off[1])

    def move_to(self, x, y):
        # 夾取到整個虛擬桌面（含所有螢幕）範圍內，避免拖到看不見
        vx, vy, vw, vh = virtual_screen_rect()
        w = max(1, self.win.winfo_width() or self.win.winfo_reqwidth())
        h = max(1, self.win.winfo_height() or self.win.winfo_reqheight())
        if vw > 0 and vh > 0:
            x = max(vx, min(x, vx + vw - w))
            y = max(vy, min(y, vy + vh - h))
        self.pos = (int(x), int(y))
        if IS_WINDOWS:
            move_window(self.win.winfo_id(), self.pos[0], self.pos[1])
        else:
            self.win.geometry(tk_pos(self.pos[0], self.pos[1]))

    def _on_modified(self, event=None):
        if self.orig.edit_modified():
            self.orig.edit_modified(False)
            self.app.schedule_translate()
            self._resize()

    def _on_enter(self, event):
        # 中文輸入法（注音/拼音）使用中時，Enter 交給 IME，不做回填
        if ime_is_open():
            return "break"
        if self.app.card_is_empty():
            self.app.forward_key_to_target(VK_RETURN)
        else:
            self.app.commit(False)
        return "break"

    def _on_backspace(self, event):
        if self.app.card_is_empty():
            return "break"  # 空卡片時忽略 Backspace，不關閉翻譯模式
        return None  # 非空時，讓 Text 預設行為刪除字元

    def _on_shift_enter(self, event):
        self.orig.insert("insert", "\n")
        return "break"

    def _on_ctrl_enter(self, event):
        self.app.commit(False)
        return "break"

    def _on_ctrl_shift_enter(self, event):
        self.app.commit(True)
        return "break"

    def set_orig(self, text):
        self.orig.delete("1.0", "end")
        if text:
            self.orig.insert("1.0", text)
        self.orig.mark_set("insert", "end")
        self.orig.edit_modified(False)

    def get_orig(self):
        return self.orig.get("1.0", "end-1c")

    def set_trans(self, text):
        self.trans.config(text=text)

    def get_trans(self):
        return self.trans.cget("text")

    def set_trans2(self, text):
        text = text or ""
        self.trans2.config(text=text)
        self.trans2.pack_forget()
        if text:
            self.trans2.pack(fill="x", side="top", padx=6, pady=(0, 4))

    def get_trans2(self):
        return self.trans2.cget("text")

    def apply_style(self):
        cfg = self.app.cfg
        self.orig_size = int(cfg.get("card_orig_size", 10))
        self.orig_color = cfg.get("card_orig_color", "#b8b8c8")
        self.trans_size = int(cfg.get("card_trans_size", 12))
        self.trans_color = cfg.get("card_trans_color", "#ffffff")
        self.orig.config(fg=self.orig_color, insertbackground=self.trans_color,
                         font=("Microsoft YaHei UI", self.orig_size))
        self.trans.config(fg=self.trans_color,
                          font=("Microsoft YaHei UI", self.trans_size, "bold"))
        self.trans2.config(fg=self.trans_color,
                           font=("Microsoft YaHei UI", self.trans_size, "bold"))
        self._resize()

    def clear(self):
        self.set_orig("")
        self.set_trans("")
        self.set_trans2("")
        self._resize()

    def show_at(self, x, y):
        self.win.deiconify()
        self._resize()
        self.move_to(x, y)

    def hide(self):
        self.win.withdraw()

    def is_visible(self):
        return self.win.state() != "withdrawn"

    def _resize(self):
        fs = tkfont.Font(font=("Microsoft YaHei UI", self.orig_size))
        ft = tkfont.Font(font=("Microsoft YaHei UI", self.trans_size, "bold"))
        MAX_W = 440
        PAD_X = 16
        PAD_Y = 10
        DRAG_H = 7
        orig = self.get_orig()
        trans = self.get_trans()
        trans2 = self.get_trans2()

        # 依最長內容決定寬度
        max_px = 0
        for ln in orig.split("\n"):
            max_px = max(max_px, fs.measure(ln))
        for t in (trans, trans2):
            for ln in (t or "").split("\n"):
                max_px = max(max_px, ft.measure(ln))
        wrap = max(60, min(max_px, MAX_W))

        self.trans.config(wraplength=wrap)
        self.trans2.config(wraplength=wrap)
        char_w = max(1, fs.measure("0"))
        self.orig.config(width=max(2, int(wrap / char_w)), height=1)

        # 讓 Tk 計算實際折行後，依顯示行數設定高度
        self.win.update_idletasks()
        try:
            o_lines = int(self.orig.count("1.0", "end-1c", "displaylines"))
        except Exception:
            o_lines = max(1, len(orig.split("\n")))
        self.orig.config(height=max(1, o_lines))
        self.win.update_idletasks()

        # 依實際需求尺寸設定視窗大小
        parts = [self.orig, self.trans]
        if trans2:
            parts.append(self.trans2)
        req_w = max(p.winfo_reqwidth() for p in parts) + PAD_X
        req_h = sum(p.winfo_reqheight() for p in parts) + PAD_Y + DRAG_H
        self.win.geometry("{}x{}".format(int(req_w), int(req_h)))
        # Tk 的 geometry 可能把視窗移回舊位置，用 Win32 重新套用實際位置
        if IS_WINDOWS:
            move_window(self.win.winfo_id(), self.pos[0], self.pos[1])


# ---------- 主程式 ----------
class TranslatorApp:
    def __init__(self, root, cfg):
        self.root = root
        self.cfg = cfg
        self.events = queue.Queue()
        self.mode_on = False
        self.target_hwnd = None
        self.debounce_job = None
        self.translate_gen = 0
        self.hint_job = None
        self.hook = None
        self._tray = None
        self._tray_lit = None
        self._tray_dim = None
        self._focus_key = None
        self._fallback_pos = None
        self._last_commit_hwnd = None

        self.source_var = tk.StringVar(value=cfg.get("source_lang", "自動偵測"))
        self.target_var = tk.StringVar(value=cfg.get("target_lang", "英文"))
        self.target2_var = tk.StringVar(value=cfg.get("target_lang2", "") or "（無）")
        self.style_var = tk.StringVar(value=cfg.get("style", "學術"))
        self.status_var = tk.StringVar(value="翻譯模式：關閉")
        self.style_var.trace_add("write", self._on_style_change)
        self.target2_var.trace_add("write", self._on_target2_change)

        self._build_help_window()
        self.card = FloatingCard(root, self)

    # ---------- 主視窗 ----------
    def _build_help_window(self):
        root = self.root
        root.title("{} v{} — 使用說明".format(APP_NAME, APP_VERSION))
        root.geometry("500x580")
        root.minsize(420, 460)
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass

        top = ttk.Frame(root, padding=(12, 10))
        top.pack(fill="x")
        ttk.Label(top, text=APP_NAME,
                  font=("Microsoft YaHei UI", 15, "bold")).pack(side="left")
        ttk.Label(top, text="v" + APP_VERSION,
                  foreground="#888888").pack(side="left", padx=(8, 0))

        bar = ttk.Frame(root, padding=(12, 2))
        bar.pack(fill="x")
        ttk.Button(bar, text="設定", width=9, command=self.open_settings).pack(side="left")
        ttk.Button(bar, text="贊助", width=9, command=self.open_sponsor).pack(side="left", padx=6)
        ttk.Button(bar, text="關於與說明", width=11,
                   command=self.open_website).pack(side="left")
        ttk.Button(bar, text="退出", width=7, command=self.quit_app).pack(side="right")

        tip = tk.Text(root, wrap="word", bg="#f7f7f7", relief="flat",
                      font=("Microsoft YaHei UI", 10), padx=12, pady=10)
        tip.pack(fill="both", expand=True, padx=12, pady=(8, 4))
        tip.insert("1.0", HELP_TEXT)
        tip.config(state="disabled")

        ttk.Label(root, textvariable=self.status_var,
                  foreground="#666666").pack(anchor="w", padx=14, pady=(0, 8))

        root.protocol("WM_DELETE_WINDOW", self.hide_main)

    def open_website(self):
        webbrowser.open(WEBSITE_URL)

    def open_sponsor(self):
        webbrowser.open(SPONSOR_URL)

    # ---------- 焦點判斷 ----------
    def is_focus_our_window(self):
        if not IS_WINDOWS:
            return True
        fg = user32.GetForegroundWindow()
        if not fg:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
        return pid.value == os.getpid()

    def _card_position(self):
        # 1) 系統文字游標（caret）下方 —— 標準 Win32 輸入框最準
        r = get_caret_rect()
        if r:
            return r[0], r[3] + 2
        # 2) 抓不到系統 caret（Chrome/Electron 等自繪游標）時，
        #    用最近一次點擊位置近似文字游標
        if self._fallback_pos:
            return self._fallback_pos[0], self._fallback_pos[1] + 16
        # 3) 目標輸入框下方
        if self.target_hwnd:
            wr = get_window_rect(self.target_hwnd)
            if wr:
                return wr[0], wr[3] + 8
        # 4) 預設
        return 100, 100

    def card_is_empty(self):
        return not self.card.get_orig().strip()

    def forward_key_to_target(self, vk):
        """把單一按鍵轉送給原本的輸入框（卡片為空時穿透用）。"""
        hwnd = self.target_hwnd
        if not hwnd or not IS_WINDOWS:
            return
        top = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
        inject_key(VK_MENU)
        inject_key(VK_MENU, KEYEVENTF_KEYUP)
        user32.SetForegroundWindow(top)
        time.sleep(0.03)
        user32.SetFocus(hwnd)
        time.sleep(0.03)
        inject_key(vk)
        inject_key(vk, KEYEVENTF_KEYUP)

    # ---------- 模式切換 ----------
    def toggle_mode(self):
        self.mode_on = not self.mode_on
        if self.mode_on:
            self.target_hwnd = get_focus_hwnd()
            self._focus_key = (self.target_hwnd, get_caret_rect())
            self._fallback_pos = get_cursor_pos()
            self._last_commit_hwnd = None
            self.status_var.set("翻譯模式：開啟 ｜ 在卡片輸入")
            self.card.set_orig("")
            self.card.set_trans("")
            self.card.set_trans2("")
            x, y = self._card_position()
            self.card.show_at(x, y)
            self.card.focus()  # 卡片取得焦點，可直接打字（含注音 IME）
        else:
            self.status_var.set("翻譯模式：關閉")
            self.card.hide()
            self.focus_target()  # 關閉時游標回到輸入框
        self._update_tray_icon()

    def cancel(self):
        if not self.mode_on:
            return
        self.target_hwnd = None
        self.card.clear()
        self.card.hide()
        self.status_var.set("已取消")

    def focus_card(self):
        """把焦點拉回卡片（熱鍵 Ctrl+Alt+C）。

        當你在別的輸入框點來點去之後，不必再找卡片在哪，按一下焦點就回來。
        """
        if not self.mode_on or not self.card.is_visible():
            self.status_var.set("翻譯模式未開啟")
            return
        try:
            self.card.focus()
            self.status_var.set("↩ 焦點已回到卡片")
        except Exception:
            pass

    def focus_target(self):
        """把焦點還給目標輸入框（關閉模式 / 回填後用）。"""
        hwnd = self.target_hwnd
        if not hwnd or not IS_WINDOWS:
            return
        top = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
        inject_key(VK_MENU)
        inject_key(VK_MENU, KEYEVENTF_KEYUP)
        user32.SetForegroundWindow(top)
        time.sleep(0.03)
        user32.SetFocus(hwnd)

    def schedule_translate(self):
        if self.debounce_job is not None:
            try:
                self.root.after_cancel(self.debounce_job)
            except Exception:
                pass
        self.debounce_job = self.root.after(self.cfg.get("debounce_ms", 500), self._do_translate)

    def _do_translate(self):
        self.debounce_job = None
        text = self.card.get_orig().strip()
        self.translate_gen += 1
        gen = self.translate_gen
        if not text:
            self.card.set_trans("")
            return
        if not self.cfg.get("api_key"):
            self.status_var.set("⚠ 未設定 API Key，請至「設定」填入")
            return
        src = self.source_var.get()
        tgt = self.target_var.get()
        tgt2 = self.target2_var.get()
        if tgt2 == "（無）":
            tgt2 = ""
        cfg_snapshot = dict(self.cfg)
        cfg_snapshot["style"] = self.style_var.get()
        cfg_snapshot["target_lang2"] = tgt2
        threading.Thread(target=self._worker,
                         args=(text, src, tgt, cfg_snapshot, gen), daemon=True).start()

    def _worker(self, text, src, tgt, cfg_snapshot, gen):
        try:
            result = call_translate(text, src, tgt, cfg_snapshot)
            self.events.put(("result", result, gen))
        except Exception as e:
            self.events.put(("error", str(e), gen))

    def _on_style_change(self, *a):
        self.cfg["style"] = self.style_var.get()
        save_config(self.cfg)

    def _on_target2_change(self, *a):
        v = self.target2_var.get()
        self.cfg["target_lang2"] = "" if v == "（無）" else v
        save_config(self.cfg)

    # ---------- 提交 ----------
    def commit(self, original_not_translation):
        if original_not_translation:
            text = self.card.get_orig()
        else:
            if not self.card.get_orig().strip():
                self.status_var.set("尚未輸入內容")
                return
            text = self.card.get_trans()
        text = (text or "").strip()
        if not text or text.startswith("⚠"):
            self.status_var.set("沒有可回填的內容")
            return
        hwnd = self.target_hwnd or (get_focus_hwnd() if not self.is_focus_our_window() else None)

        # 英文這類以空格分詞的語言：連續回填時自動補一個空格
        if (self.cfg.get("auto_space", True) and not original_not_translation
                and hwnd and self._should_auto_space(hwnd)):
            text = " " + text

        set_clipboard_text(text)
        if hwnd and IS_WINDOWS:
            paste_into(hwnd)
            self.status_var.set("✓ 已回填至輸入框")
            self._last_commit_hwnd = hwnd
        else:
            self.status_var.set("✓ 已複製到剪貼簿（無目標輸入框）")
        self.card.clear()
        self.card.focus()  # 卡片保持開啟並聚焦，可繼續輸入下一句

    # 不使用空格分詞的語言（補空格反而錯誤）
    NO_SPACE_LANGS = ("繁體中文", "簡體中文", "日文")

    def _should_auto_space(self, hwnd):
        """判斷譯文前面是否該補一個空格。

        其他應用程式的輸入框內容無法可靠讀取，因此採用安全的近似：
        對「同一個輸入框」連續回填第二次以上時補一個空格
        （此時前一次回填的譯文就在游標前面）。
        """
        if self.target_var.get() in self.NO_SPACE_LANGS:
            return False
        return hwnd == self._last_commit_hwnd

    def copy_translation(self):
        text = self.card.get_trans().strip()
        if not text or text.startswith("⚠"):
            return
        set_clipboard_text(text)
        self.status_var.set("✓ 已複製譯文到剪貼簿")

    def copy_translation2(self):
        text = self.card.get_trans2().strip()
        if not text:
            return
        set_clipboard_text(text)
        self.status_var.set("✓ 已複製第二段譯文到剪貼簿")

    # ---------- 更新檢查 ----------
    def check_update(self, manual=False):
        """背景檢查更新；失敗一律靜默（沒網路不能出錯）。"""
        if GITHUB_REPO.startswith("YOUR_"):
            if manual:
                messagebox.showinfo("檢查更新", "尚未設定更新來源（GITHUB_REPO）。")
            return

        def worker():
            info = None
            try:
                req = urllib.request.Request(
                    UPDATE_URL,
                    headers={"User-Agent": "{}/{}".format(APP_NAME, APP_VERSION)})
                with urllib.request.urlopen(req, timeout=6) as r:
                    info = json.loads(r.read().decode("utf-8"))
            except Exception:
                info = None
            self.root.after(0, lambda: self._on_update_result(info, manual))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_result(self, info, manual):
        if not info:
            if manual:
                messagebox.showinfo("檢查更新", "無法取得更新資訊，請確認網路連線。")
            return
        latest = str(info.get("version", "0"))
        if not is_newer(latest, APP_VERSION):
            if manual:
                messagebox.showinfo("檢查更新",
                                    "目前已是最新版本（v{}）。".format(APP_VERSION))
            return
        notes = info.get("notes", "")
        url = info.get("url") or RELEASES_URL
        if manual or info.get("mandatory"):
            if messagebox.askyesno(
                    "發現新版本",
                    "有新版本 v{}（目前 v{}）：\n\n{}\n\n要前往下載頁嗎？".format(
                        latest, APP_VERSION, notes)):
                webbrowser.open(url)
        else:
            self.status_var.set("⬆ 有新版本 v{}（系統匣右鍵 → 檢查更新）".format(latest))

    # ---------- 事件迴圈 ----------
    def _watch_focus(self):
        """模式開啟時偵測焦點變化：切換到別的輸入框就更新回填目標與卡片位置。"""
        if self.mode_on:
            try:
                if not self.is_focus_our_window():
                    hwnd = get_focus_hwnd()
                    r = get_caret_rect()
                    key = (hwnd, r)
                    if key != self._focus_key:
                        self._focus_key = key
                        self._fallback_pos = get_cursor_pos()
                        if hwnd:
                            self.target_hwnd = hwnd
                            if self.card.is_visible():
                                x, y = self._card_position()
                                self.card.move_to(x, y)
            except Exception:
                pass
        self.root.after(250, self._watch_focus)

    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                try:
                    self._dispatch(ev)
                except Exception as e:
                    self.status_var.set("⚠ 錯誤：" + str(e))
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def _dispatch(self, ev):
        kind = ev[0]
        if kind == "toggle":
            self.toggle_mode()
        elif kind == "focus_card":
            self.focus_card()
        elif kind == "result":
            if ev[2] == self.translate_gen:
                self.card.set_trans(ev[1])
                self.card._resize()
                self.status_var.set("✓ 翻譯完成")
        elif kind == "error":
            if ev[2] == self.translate_gen:
                self.status_var.set("⚠ " + ev[1])  # 錯誤只顯示在狀態列（卡片不放說明文字）
        elif kind == "error_hook":
            self.status_var.set("⚠ 鍵盤掛鉤安裝失敗，攔截功能不可用")

    # ---------- 設定 ----------
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("{} 設定".format(APP_NAME))
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.resizable(False, False)
        win.grab_set()

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        # ==================== 分頁一：翻譯 ====================
        tf = ttk.Frame(nb, padding=14)
        nb.add(tf, text="   翻譯   ")

        endpoint_var = tk.StringVar(value=self.cfg.get("endpoint", ""))
        key_var = tk.StringVar(value=self.cfg.get("api_key", ""))
        model_var = tk.StringVar(value=self.cfg.get("model", ""))
        debounce_var = tk.StringVar(value=str(self.cfg.get("debounce_ms", 500)))
        provider_var = tk.StringVar(value="自訂…")
        for _p in PROVIDERS:                      # 依現有 API 網址反推服務
            if _p[1] and _p[1] == self.cfg.get("endpoint", ""):
                provider_var.set(_p[0])
                break

        link_state = {"url": ""}
        r = 0

        ttk.Label(tf, text="翻譯服務").grid(row=r, column=0, sticky="w", padx=6, pady=5)
        prov_box = ttk.Combobox(tf, textvariable=provider_var, values=PROVIDER_NAMES,
                                state="readonly", width=32)
        prov_box.grid(row=r, column=1, sticky="we", padx=6, pady=5)
        link_btn = ttk.Button(tf, text="取得 API Key",
                              command=lambda: webbrowser.open(link_state["url"])
                              if link_state["url"] else None)
        link_btn.grid(row=r, column=2, padx=6)
        r += 1

        def field(label, var, show=None):
            nonlocal r
            ttk.Label(tf, text=label).grid(row=r, column=0, sticky="w", padx=6, pady=5)
            ttk.Entry(tf, textvariable=var, width=32, show=show).grid(
                row=r, column=1, columnspan=2, sticky="we", padx=6, pady=5)
            r += 1

        field("API 網址", endpoint_var)
        field("API Key", key_var, show="*")

        ttk.Label(tf, text="模型").grid(row=r, column=0, sticky="w", padx=6, pady=5)
        model_box = ttk.Combobox(tf, textvariable=model_var, width=32)
        model_box.grid(row=r, column=1, columnspan=2, sticky="we", padx=6, pady=5)
        r += 1

        ttk.Label(tf, foreground="#888888", wraplength=390, justify="left",
                  text="模型可直接輸入；清單為該服務的常見選項。"
                  ).grid(row=r, column=1, columnspan=2, sticky="w", padx=6, pady=(0, 4))
        r += 1

        ttk.Separator(tf, orient="horizontal").grid(
            row=r, column=0, columnspan=3, sticky="we", pady=10)
        r += 1

        def combo_row(label, var, values):
            nonlocal r
            ttk.Label(tf, text=label).grid(row=r, column=0, sticky="w", padx=6, pady=5)
            ttk.Combobox(tf, textvariable=var, values=values, state="readonly",
                         width=32).grid(row=r, column=1, columnspan=2,
                                        sticky="we", padx=6, pady=5)
            r += 1

        combo_row("來源語言", self.source_var, SOURCE_LANGS)
        combo_row("目標語言", self.target_var, TARGET_LANGS)
        combo_row("第二外語", self.target2_var, ["（無）"] + TARGET_LANGS)
        ttk.Label(tf, foreground="#888888", wraplength=390, justify="left",
                  text="第二外語：原文已是上面「目標語言」時，改用此語言翻譯；選「（無）」＝停用。"
                  ).grid(row=r, column=1, columnspan=2, sticky="w", padx=6, pady=(0, 4))
        r += 1

        combo_row("翻譯風格", self.style_var, STYLES)

        ttk.Label(tf, text="延遲(毫秒)").grid(row=r, column=0, sticky="w", padx=6, pady=5)
        ttk.Entry(tf, textvariable=debounce_var, width=32).grid(
            row=r, column=1, columnspan=2, sticky="we", padx=6, pady=5)
        r += 1

        def on_provider(*a):
            """切換服務時自動帶入 API 網址與模型清單。"""
            for p in PROVIDERS:
                if p[0] == provider_var.get():
                    if p[1]:
                        endpoint_var.set(p[1])
                    model_box["values"] = p[2]
                    if p[2]:
                        model_var.set(p[2][0])
                    link_state["url"] = p[3]
                    break

        prov_box.bind("<<ComboboxSelected>>", on_provider)

        # ==================== 分頁二：卡片外觀 ====================
        af = ttk.Frame(nb, padding=14)
        nb.add(af, text="   卡片外觀   ")

        orig_size_var = tk.StringVar(value=str(self.cfg.get("card_orig_size", 10)))
        orig_color_var = tk.StringVar(value=self.cfg.get("card_orig_color", "#b8b8c8"))
        trans_size_var = tk.StringVar(value=str(self.cfg.get("card_trans_size", 12)))
        trans_color_var = tk.StringVar(value=self.cfg.get("card_trans_color", "#ffffff"))

        # 即時預覽（與實際卡片同色）
        prev_outer = tk.Frame(af, bg="#3a3a48", padx=1, pady=1)
        prev_outer.grid(row=0, column=0, columnspan=4, sticky="we", pady=(0, 16))
        prev_inner = tk.Frame(prev_outer, bg="#1c1c28")
        prev_inner.pack(fill="both", expand=True)
        prev_orig = tk.Label(prev_inner, text="Hello, how are you?",
                             bg="#1c1c28", justify="left", anchor="w")
        prev_orig.pack(fill="x", padx=12, pady=(8, 2))
        prev_trans = tk.Label(prev_inner, text="你好，你好嗎？",
                              bg="#1c1c28", justify="left", anchor="w")
        prev_trans.pack(fill="x", padx=12, pady=(0, 8))

        def refresh_preview(*a):
            try:
                osz = max(6, min(48, int(orig_size_var.get())))
            except Exception:
                osz = int(self.cfg.get("card_orig_size", 10))
            try:
                tsz = max(6, min(48, int(trans_size_var.get())))
            except Exception:
                tsz = int(self.cfg.get("card_trans_size", 12))
            prev_orig.config(fg=orig_color_var.get() or "#b8b8c8",
                             font=("Microsoft YaHei UI", osz))
            prev_trans.config(fg=trans_color_var.get() or "#ffffff",
                              font=("Microsoft YaHei UI", tsz, "bold"))

        def color_btn(parent, var):
            b = tk.Button(parent, width=6, relief="groove", cursor="hand2",
                          command=lambda: _pick(var))

            def upd(*a):
                try:
                    b.config(bg=var.get())
                except Exception:
                    pass
            var.trace_add("write", upd)
            upd()
            return b

        def _pick(var):
            c = colorchooser.askcolor(color=var.get() or "#ffffff", parent=win)
            if c and c[1]:
                var.set(c[1])
            refresh_preview()

        def size_spin(parent, var):
            var.trace_add("write", refresh_preview)
            sp = ttk.Spinbox(parent, from_=6, to=48, width=6,
                             textvariable=var, command=refresh_preview)
            sp.bind("<KeyRelease>", refresh_preview)
            return sp

        ttk.Label(af, text="輸入文字").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        size_spin(af, orig_size_var).grid(row=1, column=1, sticky="w", pady=6)
        ttk.Label(af, text="字級").grid(row=1, column=2, sticky="e", padx=(10, 6), pady=6)
        color_btn(af, orig_color_var).grid(row=1, column=3, sticky="w", pady=6)

        ttk.Label(af, text="翻譯文字").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
        size_spin(af, trans_size_var).grid(row=2, column=1, sticky="w", pady=6)
        ttk.Label(af, text="字級").grid(row=2, column=2, sticky="e", padx=(10, 6), pady=6)
        color_btn(af, trans_color_var).grid(row=2, column=3, sticky="w", pady=6)

        ttk.Label(af, foreground="#888888", wraplength=390, justify="left",
                  text="點顏色方塊開啟調色盤；上方即為實際卡片樣貌，調整會立即更新。"
                  ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(12, 0))

        # ==================== 按鈕 ====================
        btns = ttk.Frame(win, padding=(10, 0, 10, 10))
        btns.pack(fill="x")

        def save():
            ep = endpoint_var.get().strip()
            if not ep:
                messagebox.showwarning("設定", "API 網址不可為空", parent=win)
                return
            self.cfg["endpoint"] = ep
            self.cfg["api_key"] = key_var.get().strip()
            self.cfg["model"] = model_var.get().strip()
            self.cfg["source_lang"] = self.source_var.get()
            self.cfg["target_lang"] = self.target_var.get()
            self.cfg["style"] = self.style_var.get()
            self.cfg["target_lang2"] = ("" if self.target2_var.get() == "（無）"
                                        else self.target2_var.get())
            try:
                self.cfg["debounce_ms"] = max(200, int(debounce_var.get().strip()))
            except ValueError:
                self.cfg["debounce_ms"] = 500
            try:
                self.cfg["card_orig_size"] = max(6, min(48, int(orig_size_var.get().strip())))
            except ValueError:
                self.cfg["card_orig_size"] = 10
            try:
                self.cfg["card_trans_size"] = max(6, min(48, int(trans_size_var.get().strip())))
            except ValueError:
                self.cfg["card_trans_size"] = 12
            self.cfg["card_orig_color"] = orig_color_var.get().strip() or "#b8b8c8"
            self.cfg["card_trans_color"] = trans_color_var.get().strip() or "#ffffff"
            save_config(self.cfg)
            self.card.apply_style()
            self.status_var.set("✓ 已儲存設定")
            win.destroy()

        ttk.Button(btns, text="儲存", command=save).pack(side="right", padx=6)
        ttk.Button(btns, text="取消", command=win.destroy).pack(side="right")

        on_provider()        # 初始化 API 網址 / 模型清單 / 連結
        refresh_preview()

        # 主視窗是隱藏的，這裡要確保設定視窗能獨立顯示
        win.update_idletasks()
        win.deiconify()
        win.lift()
        try:
            win.focus_force()
        except Exception:
            pass

    # ---------- 視窗 ----------
    def hide_main(self):
        self.root.withdraw()

    def quit_app(self):
        if messagebox.askyesno("退出", "確定要完全退出即時翻譯嗎？"):
            self._quit()

    # ---------- 系統匣 ----------
    def setup_tray(self):
        if not HAS_TRAY:
            log("系統匣不可用：{}（請執行：python -m pip install --user pystray pillow）".format(TRAY_ERR))
            self.status_var.set("系統匣不可用：{}（請執行：pip install pystray pillow）".format(TRAY_ERR))
            return
        try:
            self._tray_lit = make_tray_image(True)
            self._tray_dim = make_tray_image(False)
            self._tray = pystray.Icon(
                APP_NAME.lower(), self._tray_dim,
                "{} v{}".format(APP_NAME, APP_VERSION),
                menu=pystray.Menu(
                    pystray.MenuItem("設定", self._on_tray_settings),
                    pystray.MenuItem("使用說明", self._on_tray_help),
                    pystray.MenuItem("贊助", self._on_tray_sponsor),
                    pystray.MenuItem("檢查更新", self._on_tray_update),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("退出", self._on_tray_quit),
                ),
            )
            try:
                self._tray.run_detached()
            except AttributeError:
                threading.Thread(target=self._tray.run, daemon=True).start()
            log("系統匣圖示已建立")
        except Exception as e:
            self.status_var.set("系統匣圖示啟動失敗：" + str(e))
            log("系統匣圖示啟動失敗：{}".format(e))

    def _on_tray_settings(self, icon, item):
        self.root.after(0, self.open_settings)

    def _on_tray_help(self, icon, item):
        self.root.after(0, self.show_main)

    def _on_tray_sponsor(self, icon, item):
        self.root.after(0, self.open_sponsor)

    def _on_tray_update(self, icon, item):
        self.root.after(0, lambda: self.check_update(manual=True))

    def _on_tray_quit(self, icon, item):
        self.root.after(0, self.quit_app)

    def _update_tray_icon(self):
        if HAS_TRAY and self._tray:
            try:
                self._tray.icon = self._tray_lit if self.mode_on else self._tray_dim
            except Exception:
                pass

    def show_main(self):
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.focus_force()
        except Exception:
            pass

    def _quit(self):
        if self.hook:
            try:
                self.hook.stop()
            except Exception:
                pass
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.root.destroy()


def main():
    cfg = load_config()
    enable_dpi_awareness()
    root = tk.Tk()
    log("{} v{} 啟動 ｜ 虛擬桌面 {} ｜ 設定檔 {}".format(
        APP_NAME, APP_VERSION, virtual_screen_rect(), config_path()))
    app = TranslatorApp(root, cfg)

    if IS_WINDOWS:
        app.hook = KeyboardHook(app)
        app.hook.start()

    root.withdraw()          # 啟動時只顯示系統匣圖示，不開視窗

    if not cfg.get("api_key"):
        root.after(600, app.open_settings)   # 尚未設定金鑰時才自動開設定

    app.setup_tray()
    app._poll()
    app._watch_focus()
    if cfg.get("check_update_on_start", True):
        root.after(3000, lambda: app.check_update(manual=False))
    root.mainloop()


if __name__ == "__main__":
    main()
