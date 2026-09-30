這個資料夾放網站的圖片素材，同時也是應用程式圖示與 logo 的來源。

── 由程式產生（請勿手改）──

  logo.svg              橫式 logo，深色字（淺色背景）— 網站頁首使用
  logo-white.svg        橫式 logo，白色字（深色背景）— GitHub 深色模式
  logo-mark.svg         只有圖標，無文字
      產生方式：python tools\make_logo.py
      文字已轉成向量路徑，不依賴使用者字型

  app.ico               應用程式圖示 / favicon
                        內含 16/24/32/48/64/128/256 七種尺寸
  apple-touch-icon.png  iOS / Safari 加入書籤用（180x180）
  og-image.png          社群分享預覽（1200x630）
      產生方式：python tools\make_icon.py
      設計：品牌藍漸層圓角方塊 + 白色對話框 + 翻譯雙箭頭
      32px 以下自動改用簡化的單箭頭版本

── 手動放置 ──

  demo.gif              30 秒動態展示（最能提升說服力）
  screenshot-1.png      主畫面截圖（卡片運作中）
  screenshot-2.png      設定視窗截圖

── 其他 ──

  twqr-donate.jpg       TWQR 台灣Pay 收款碼（已套用於贊助區）
  logo-draft.svg        Duolingo 風格貓頭鷹草稿（暫不採用，見開發日誌第 25 章）