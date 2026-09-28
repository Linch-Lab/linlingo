# 即時翻譯（Windows 全域攔截式輸入）

按下全域熱鍵 **Ctrl+Alt+T** 開啟「翻譯模式」後，一個**極簡、半透明、隨文字量自動變大**的浮動卡片
會出現在**文字輸入游標旁**，輸入游標自動跳進卡片；直接在卡片打字即時顯示「原文 + 翻譯」，
再按熱鍵把翻譯結果**回填**進原本的輸入框。

純 Python 標準庫 + tkinter；系統匣圖示需另裝 pystray / Pillow（可選，未裝則無圖示）。

---

## 一、操作方式

| 動作 | 熱鍵 |
|---|---|
| 開啟 / 關閉翻譯模式 | `Ctrl+Alt+T` |
| 回填翻譯（不送出） | `Enter` |
| 送出（卡片清空後再按 Enter） | `Enter` |
| 回填**原文** | `Ctrl+Shift+Enter` |
| 換行（多行訊息） | `Shift+Enter` |
| 取消（清空卡片） | `Esc` |

流程：

1. 點擊任意應用程式的輸入框（聊天框、表單、搜尋欄…）定位文字游標
2. 按 `Ctrl+Alt+T` → 浮動卡片出現在**游標旁**，輸入游標**自動跳進卡片**
3. 直接在卡片打字 → 即時顯示翻譯並自動變大
4. 按 `Enter` → 翻譯結果回填到輸入框（**不送出**）
5. 卡片清空後再按 `Enter` → 送出（等同在輸入框按 Enter）
6. 再按 `Ctrl+Alt+T` 關閉翻譯模式（恢復正常打字）

> `Backspace`：卡片有字時刪字；**卡片清空後再按一次 = 關閉翻譯模式**（焦點回到輸入框，繼續刪輸入框的字）。

> 若關閉了自動聚焦（或使用 `manual` 攔截模式），浮動卡片也可直接**點進去**打字，
> 打完同樣用 `Ctrl+Enter` 回填。拖曳「翻譯文字」區可移動卡片。

### 系統匣圖示

啟動後會在**系統匣（工作列通知區域，輸入法旁）**出現小圖示：

- 翻譯模式**開啟** → 圖示**點亮**（藍色）；**關閉** → **反灰**
- **右鍵**圖示 → 「設定」「使用說明」「退出」

## 二、環境需求

- Windows 10 / 11
- Python 3.8 以上（含 tkinter，官方安裝版預設都有）
- （選用）系統匣圖示：`pystray` + `Pillow`

## 三、安裝步驟

1. 安裝 Python（https://www.python.org/downloads/ ，勾選 **Add Python to PATH**）
2. （選用，要有工作列圖示才需執行）`pip install pystray pillow`
3. 到 [DeepSeek 開放平台](https://platform.deepseek.com/) 註冊並建立 **API Key**
4. 雙擊 `run.bat`（或指令 `python app.py`）
5. 首次啟動自動跳出「設定」，填入 API 網址 / Key / 模型，儲存
6. 依「操作方式」開始使用

## 四、設定說明

### 攔截模式（intercept_mode）

| 值 | 行為 |
|---|---|
| `all`（預設） | 翻譯模式開啟時攔截**所有**輸入（最可靠，適合 Chrome/Electron 等現代應用） |
| `auto` | 只攔截「看起來像輸入框」的控制項（Win32 傳統視窗較準） |
| `manual` | 不攔截，直接點浮動卡片打字，再按熱鍵回填 |

### 換成其他 API（OpenAI / Ollama / 通義千問…）

只要接口是 **OpenAI 相容** 的 `/chat/completions` 即可，改「設定」三個欄位：

| 服務 | API 網址 | 模型 |
|---|---|---|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| OpenAI | `https://api.openai.com` | `gpt-4o-mini` |
| 阿里雲通義 | `https://dashscope.aliyuncs.com/compatible-mode` | `qwen-plus` |
| Ollama 本地 | `http://localhost:11434` | `qwen2.5:7b` |

### 自訂熱鍵（編輯 `config.json`）

修飾鍵相加：`ALT=1`、`CTRL=2`、`SHIFT=4`、`WIN=8`。

| 欄位 | 意義 | 預設 |
|---|---|---|
| `toggle_vk` / `toggle_mods` | 開關翻譯模式 | `84`(T) / `3`(Ctrl+Alt) |
| `commit_vk` / `commit_mods` | 回填翻譯 | `13`(Enter) / `2`(Ctrl) |
| `commit_orig_mods` | 回填原文（同 Enter 鍵） | `6`(Ctrl+Shift) |
| `cancel_vk` | 取消 | `27`(Esc) |

常用虛擬鍵碼：A=65、B=66、D=68、S=83、T=84、Space=32、Enter=13、F8=119。

## 五、常見問題

- **打字沒被攔截**：確認翻譯模式已開啟；若在 Chrome/Electron 中無效，把攔截模式設為 `all`（預設即是）。
- **中文輸入法（IME）組字異常**：低階攔截對 IME 組字支援有限，可直接**點擊浮動卡片**用 IME 打字，再 `Ctrl+Enter` 回填。
- **回填沒貼到正確位置**：回填前不要切換視窗；若失敗可手動 `Ctrl+V`（譯文已自動複製到剪貼簿）。
- **熱鍵衝突**：改 `config.json` 裡的熱鍵（見上表）。
- **API 401**：Key 錯誤或過期；**402**：餘額不足；**網路錯誤**：檢查防火牆/代理。
- **關閉主視窗（✕）只是隱藏**，程式仍在背景；要退出請按主視窗「退出」。

## 六、打包成單一 .exe

直接雙擊 `build.bat`（會自動安裝 PyInstaller 並打包），或手動執行：

```bat
python -m pip install --user pyinstaller pystray pillow
python -m PyInstaller --onefile --windowed --name Translator --hidden-import pystray._win32 --collect-all pystray app.py
```

打包後在 `dist\Translator.exe`，可複製到任何電腦直接執行（**免裝 Python**）。

> PyInstaller 會把 pystray / Pillow 一起封進 exe，因此 **exe 版不會有「多個 Python 環境」造成的系統匣問題**。
> 若 exe 裡的系統匣圖示仍不顯示，在打包指令再加上 `--copy-metadata pystray`。
