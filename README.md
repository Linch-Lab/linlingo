<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
  <img alt="LinLingo" src="assets/logo.svg" width="240">
</picture>

# LinLingo

Windows 全域熱鍵即時翻譯工具。

在任何輸入框按 <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>T</kbd>，游標旁會出現一張半透明小卡片；
用**你自己的語言**打字，立即看到翻譯，按 <kbd>Enter</kbd> 把譯文回填到原本的輸入框。
不必切換視窗、不必複製貼上。

**下載**：[GitHub Releases](https://github.com/Linch-Lab/linlingo/releases/latest)

> **為什麼不攔截鍵盤？**
> 大多數同類工具用低階鍵盤掛鉤攔截打字，這會讓**中文／日文／韓文輸入法無法組字**。
> LinLingo 改為「卡片本身即輸入面」，因此注音、拼音都能正常使用。

---

## 專案結構

```
linlingo/                          ← 倉庫根目錄 = 網站根目錄
├── index.html / 404.html         官網（純靜態單頁，無 JavaScript）
├── .htaccess / robots.txt
├── sitemap.xml / assets/
├── latest.json                   應用內更新檢查的來源
├── app/                          Windows 應用程式
│   ├── app.py                    主程式（單一檔案）
│   ├── run.bat                   啟動（除錯用，會顯示命令列）
│   ├── LinLingo.vbs              啟動（無視窗）
│   ├── build.bat / clean.bat     建置與清理
│   ├── version.txt               版本資訊資源
│   └── releases/                 發行版本說明
├── .github/workflows/            CI：tag → 自動建置並發佈 Release
└── README.md / CHANGELOG.md / LICENSE / 開發日誌.md / 部署網站.md
```

網站放在根目錄，是為了讓 **Hostinger 的 Git 匯入**能直接把倉庫內容當成網站根目錄；
應用程式碼則全部收在 `app/`，兩者互不干擾。

---

## 快速開始

### 方法一：下載執行檔（推薦，免裝 Python）

1. 到 [Releases](https://github.com/Linch-Lab/linlingo/releases/latest) 下載 `LinLingo-win64.zip`
2. 解壓縮，執行 `LinLingo.exe`
3. 系統匣圖示右鍵 →「設定」→ 填入 API Key

### 方法二：從原始碼執行

需先安裝 Python 3.8+（安裝時勾選 **Add Python to PATH**）。

```bat
cd app
run.bat          :: 除錯用，會顯示命令列視窗
LinLingo.vbs     :: 無視窗啟動
```

系統匣圖示需額外安裝：`pip install pystray pillow`

---

## 操作方式

| 熱鍵 | 功能 |
|---|---|
| `Ctrl+Alt+T` | 開啟 / 關閉翻譯模式 |
| `Ctrl+Alt+C` | 把焦點拉回卡片（焦點跑到別的視窗時用） |
| `Enter` | 回填翻譯；卡片清空後再按 = 送出 |
| `Ctrl+Enter` | 只回填、不送出 |
| `Ctrl+Shift+Enter` | 回填原文 |
| `Shift+Enter` | 換行 |
| `Esc` | 取消、清空卡片 |

**流程**：點擊輸入框 → 按 `Ctrl+Alt+T` → 卡片出現在游標旁並取得焦點 → 在卡片打字 → `Enter`

**特色**：

- 點擊其他輸入框時，**卡片與回填目標會自動跟隨**
- 卡片可拖曳、隨內容自動縮放、半透明
- 翻譯成英文等以空格分詞的語言時，連續回填會自動補空格
- 支援多螢幕（含負座標與混合 DPI）

---

## 設定

系統匣圖示右鍵 →「設定」，分為兩個分頁。

### 翻譯

| 欄位 | 說明 |
|---|---|
| 翻譯服務 | 下拉選單，共 14 家 OpenAI 相容服務 + 自訂 |
| API 網址 | 選擇服務時自動帶入 |
| API Key | 你的金鑰 |
| 模型 | 下拉選單（可自行輸入） |
| 來源語言 | 預設「自動偵測」 |
| 目標語言 | 預設「英文」 |
| 第二外語 | 原文已是目標語言時，改翻成此語言（選「（無）」＝停用） |
| 翻譯風格 | 學術（預設）／商務／閒聊 |
| 延遲（毫秒） | 停止輸入後多久開始翻譯 |

內建服務：DeepSeek、OpenAI、阿里雲通義千問、智譜 GLM、Kimi（Moonshot）、
矽基流動 SiliconFlow、騰訊混元、火山方舟（豆包）、MiniMax、Groq、
Mistral、OpenRouter、Ollama（本地）、LM Studio（本地）。

### 卡片外觀

輸入文字與翻譯文字的**字級**（微調器）與**顏色**（點色塊開調色盤），
上方有**即時預覽**，調整立刻反映。

### 設定檔位置

```
%APPDATA%\LinLingo\config.json
```

更新或重裝都不會遺失。若要改為可攜模式，在 `LinLingo.exe` 旁建立一個空檔案
`portable.flag`，設定就會存在程式資料夾內。

### 完全本地部署（Ollama）

免費、離線、資料不出你的電腦。

| 欄位 | 值 |
|---|---|
| API 網址 | `http://localhost:11434/v1` |
| API Key | `ollama`（本地不驗證，隨便填） |
| 模型 | `qwen2.5:7b` |

---

## 開發

```bat
cd app
build.bat        :: 建置 exe，輸出到 app\releases\v<版本>\
clean.bat        :: 清除中間產物（不會動 releases\）
```

**版本號的唯一來源**是 `app/app.py` 的 `APP_VERSION`，
`build.bat` 與 GitHub Actions 都會自動讀取。

### 發佈流程

```bat
git tag v1.0.0
git push origin v1.0.0
```

推送標籤後，`.github/workflows/release.yml` 會在 GitHub 上自動建置
`LinLingo-win64.zip`、產生 `SHA256SUMS.txt` 並建立 Release。

### 驗證下載檔

```bat
certutil -hashfile LinLingo-win64.zip SHA256
```

與 Release 中的 `SHA256SUMS.txt` 比對即可。

---

## 其他文件

| 文件 | 內容 |
|---|---|
| [開發日誌](開發日誌.md) | 完整技術記錄、問題根因與決策歷程 |
| [變更紀錄](CHANGELOG.md) | 各版本的新增 / 修正 / 已知限制 |
| [網站部署指南](部署網站.md) | Hostinger 部署與 GitHub 自動同步 |

---

## 贊助

LinLingo 完全免費、開源、**沒有廣告、沒有追蹤、沒有付費版本**。
如果它替你省下了一些時間，歡迎請我喝一杯咖啡。

| 方式 | 連結 |
|---|---|
| Ko-fi | https://ko-fi.com/bill_linch |
| TWQR 台灣Pay | [官網贊助區](https://linlingo.billlinch.com/#sponsor) 掃碼即付 |

贊助者名單：[SUPPORTERS.md](SUPPORTERS.md)

**我不會做的事**：不把功能鎖在贊助後面、不加廣告或追蹤、不情緒勒索、不讓贊助者插隊。

---

## 授權

[MIT License](LICENSE)
