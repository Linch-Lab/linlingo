# 變更紀錄

本專案採用 [語意化版本](https://semver.org/lang/zh-TW/)（MAJOR.MINOR.PATCH）
與 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/) 格式。

- **MAJOR**：不相容的變更（例如設定檔格式需遷移）
- **MINOR**：新增功能（向後相容）
- **PATCH**：錯誤修正

---

## [Unreleased]

### 規劃中

- 首次啟動引導精靈（選語言 → 填 API Key → 測試連線）
- UI Automation 精確文字游標定位（Chrome / Electron）
- 翻譯歷史與常用詞

---

## [1.0.1] - 2026-09-28

### 修正

- **PowerPoint 中 `Ctrl+Enter` 無法回填**：該鍵原本是卡片視窗的按鍵綁定，
  一旦焦點被目標程式搶走就失效，反而觸發 PowerPoint 自己的 `Ctrl+Enter`
  快速鍵（切換版面配置／新增投影片），把輸入打断
- 回填後立刻搶回焦點，導致 PowerPoint 這類較重的程式來不及完成貼上
  （現在改為**延後 180ms** 再收回焦點）
- 加入 350ms 去重鎖，避免全域熱鍵與卡片按鍵同時觸發造成重複回填

### 新增

- 全域熱鍵 **`Ctrl+Alt+Enter`**：焦點在任何程式都能直接插入譯文
- 應用程式內新增官網連結：
  - 說明視窗底部：「使用說明 / 翻譯引擎教學 / 常見問題 / 問題回報」
  - 設定頁的翻譯引擎教學連結
- 設定新增 `commit_global_vk` / `commit_global_mods`（可自訂隨處插入的熱鍵）

---

## [1.0.0] - 2026-09-28

首個公開發行版本。

### 新增

**核心翻譯**

- 全域熱鍵 `Ctrl+Alt+T` 開關翻譯模式（`RegisterHotKey`，可自訂）
- 極簡半透明浮動卡片，緊貼文字游標、隨內容自動縮放、可拖曳
- **完整支援中文輸入法（注音 / 拼音）**：卡片即輸入面，不攔截鍵盤
- 翻譯風格：學術（預設）／商務／閒聊，以提示詞方式送給模型
- 第二外語條件翻譯：原文已是目標語言時改翻成第二語言
- 英譯等以空格分詞的語言，連續回填時自動補一個空格

**操作與介面**

- 全域熱鍵 `Ctrl+Alt+C`：把焦點拉回卡片
- 啟動時只顯示系統匣圖示，不彈出視窗
- 啟動完全不顯示命令列視窗
- 系統匣右鍵選單：設定／使用說明／贊助／檢查更新／退出
- 主視窗為「使用說明」頁，含「關於與說明」開啟官網
- 分頁式設定頁：翻譯 / 卡片外觀
- 翻譯服務與模型皆為**下拉選單**（內建 14 家 OpenAI 相容服務）
- 卡片外觀以圖像化設定（字級微調器、調色盤），並提供**即時預覽**
- 切換輸入框自動跟隨：點擊其他輸入框時更新回填目標與卡片位置

**系統整合**

- 系統匣圖示：開啟時點亮、關閉時反灰
- 應用內更新檢查（啟動時背景檢查 + 手動檢查）
- 設定檔存於 `%APPDATA%\PopLingo`（更新不遺失），並支援可攜模式
- 設定檔版本與遷移機制（`config_version` / `migrate_config`）
- OpenAI 相容 API，可自由替換 DeepSeek / OpenAI / 阿里雲通義 / 智譜 GLM /
  Kimi / SiliconFlow / 騰訊混元 / 火山方舟 / MiniMax / Groq / Mistral /
  OpenRouter / Ollama / LM Studio

**多螢幕**

- 支援負座標（左側、上方螢幕）與虛擬桌面邊界夾取
- 每螢幕 DPI 感知（混合縮放比例）

**發佈**

- 官網（純靜態、無 JavaScript，可直接部署至虛擬主機）
- `build.bat` 一鍵建置並歸檔至 `releases\v<版本>\`
- `clean.bat` 清除中間產物
- `publish.bat` 一鍵推送至 GitHub
- GitHub Actions：推送 tag 自動建置並發佈 Release

### 修正

- 全域熱鍵偵測不到 Alt（低階掛鉤回報 `VK_LMENU`，改用 `RegisterHotKey`）
- 注入按鍵被自家鍵盤掛鉤攔截（改用 `dwExtraInfo` 標記放行）
- 多螢幕往上拖曳時卡片跳到同螢幕下緣（Tk geometry 負座標語意陷阱，改用 `SetWindowPos`）
- 卡片文字被邊框裁切（改用實際需求尺寸計算）
- 系統匣圖示在多 Python 環境下不顯示（改用同一解譯器安裝）
- 設定視窗無法獨立顯示（移除 `transient`，改為明確 `deiconify`）
- 卡片外觀預覽未即時更新（修正中斷條件並補上事件綁定）
- 只有兩三個中文字時被誤翻成第二外語（提示詞規則明確化）
- DeepSeek 模型名稱更新為 `deepseek-flash` / `deepseek-v4-pro`，
  並在 DeepSeek 端點關閉思考模式以降低延遲

### 已知限制

- Chrome / Electron 的文字游標為自繪，位置採「點擊位置」近似
  （精確定位需 UI Automation，列為後續工作）
- 變更翻譯風格後需修改文字才會以新風格重新翻譯
- 僅支援 Windows 10 / 11（64 位元）
- 需自備 API Key，或改用 Ollama 本地模型
- 未購買程式碼簽章，Windows SmartScreen 會顯示警告
