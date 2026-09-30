# LinLingo v1.0.3

新增應用程式圖示與社群分享預覽。

## 新增

### 應用程式圖示

`LinLingo.exe` 現在有專屬圖示：品牌藍漸層圓角方塊，內含白色對話框
（浮動翻譯卡片）與雙向翻譯箭頭。

- 圖示內含 **7 種尺寸**：16 / 24 / 32 / 48 / 64 / 128 / 256
- **32px 以下自動改用簡化的單箭頭版本** —— 雙箭頭在 16px 會糊成一團，
  這是小尺寸圖示的標準做法
- 同一份圖示也用於官網的 favicon

圖示由 `tools/make_icon.py` 產生，可重現、可調整配色：

```bat
python tools\make_icon.py
```

### 社群分享預覽

官網所有頁面加上 `og:image`。分享到 Facebook、LINE、Twitter 時
會顯示 1200×630 的品牌預覽圖，而不是空白或隨機截圖。

同時加上 `apple-touch-icon`，iOS / Safari 加入書籤時顯示正確圖示。

## 修正

- `build.bat` 的圖示路徑：原本找的是 `app\assets\app.ico`，
  但圖示實際在倉庫根目錄的 `assets\`，導致圖示從未被套用

## 功能面

本版沒有功能變更。

## 檔案

| 檔案 | 說明 |
|---|---|
| `LinLingo-win64.zip` | 免安裝版，解壓後執行 `LinLingo.exe` |
| `SHA256SUMS.txt` | 檔案雜湊值，可用 `certutil -hashfile LinLingo-win64.zip SHA256` 驗證 |

## 連結

- 官網：https://linlingo.billlinch.com/
- 下載：https://linlingo.billlinch.com/download.html
- 原始碼：https://github.com/Linch-Lab/linlingo

## 授權

MIT License
