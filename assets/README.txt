這個資料夾放網站的圖片素材，同時也是應用程式圖示、logo 與示範影片的來源。

── 由程式產生（請勿手改）──

  logo.svg              橫式 logo，深色字（淺色背景）— 網站頁首使用
  logo-white.svg        橫式 logo，白色字（深色背景）— GitHub 深色模式
  logo-mark.svg         只有圖標，無文字
      產生方式：python tools\make_logo.py
      文字已轉成向量路徑，不依賴使用者字型

  app.ico               應用程式圖示（exe 用）
                        內含 16/24/32/48/64/128/256 七種尺寸
  favicon-96.png        網站圖示 PNG 版（96x96，Google 建議至少 48x48）

  另外會在倉庫根目錄產生 favicon.ico（網站圖示的標準位置，
  瀏覽器與 Google 都會自動去抓，少了它最常見的症狀就是分頁沒有圖示）
  apple-touch-icon.png  iOS / Safari 加入書籤用（180x180）
  og-image.png          社群分享縮圖（1200x630）
      產生方式：python tools\make_og_image.py
      使用正式的 logo（assets/logo-white.svg）渲染，不是另外排字
      內容置中，確保被平台裁成方形時 logo 不會被裁掉
      產生方式：python tools\make_icon.py
      設計：品牌藍漸層圓角方塊 + 白色對話框 + 翻譯雙箭頭
      32px 以下自動改用簡化的單箭頭版本

  demo.gif              操作示範，620x392、10.3 秒、64 色、0.94 MB
                        → 用於 GitHub README（markdown 不支援影片）
  demo.mp4              同一段示範，h264 crf25、只有 0.10 MB
                        → 用於官網（比 GIF 小 9.4 倍且更流暢）
  demo-poster.png       demo.mp4 的海報圖
      產生方式：python tools\make_demo_gif.py <你的錄影.mp4>
      可調參數：--start / --end / --speed / --gif-fps / --colors / --width

── 手動放置 ──

  screenshot-1.png      主畫面截圖（卡片運作中）
  screenshot-2.png      設定視窗截圖

── 其他 ──

  twqr-donate.jpg       TWQR 台灣Pay 收款碼（已套用於贊助區）
  logo-draft.svg        Duolingo 風格貓頭鷹草稿（暫不採用，見開發日誌第 25 章）