# LinLingo v1.0.0

首個公開發行版本。

## 檔案

| 檔案 | 說明 |
|---|---|
| `LinLingo-win64.zip` | 免安裝版，解壓後執行 `LinLingo.exe` |
| `SHA256SUMS.txt` | 檔案雜湊值，可用 `certutil -hashfile LinLingo-win64.zip SHA256` 驗證 |

> 本資料夾的內容由 `build.bat` 產生；若尚未建置，請先執行 `build.bat`。

## 系統需求

- Windows 10 / 11（64 位元）
- 需自備 OpenAI 相容 API Key，或使用 Ollama 本地模型

## 重點功能

- 全域熱鍵 `Ctrl+Alt+T` 開關翻譯模式
- `Ctrl+Alt+C` 把焦點拉回卡片
- 完整支援中文輸入法（注音 / 拼音）
- 翻譯風格：學術 / 商務 / 閒聊
- 第二外語條件翻譯
- 切換輸入框自動跟隨
- 多螢幕、混合 DPI
- 系統匣圖示與應用內更新檢查

## 已知限制

- 瀏覽器（Chrome / Electron）的文字游標為自繪，位置採近似值
- 僅支援 Windows

## 授權

MIT License
