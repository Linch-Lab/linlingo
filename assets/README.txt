這個資料夾放網站的圖片素材，同時也是應用程式圖示的來源。

── 由程式產生（請勿手改；改設計請改 tools\make_icon.py）──

  app.ico               應用程式圖示 / favicon
                        內含 16/24/32/48/64/128/256 七種尺寸
  apple-touch-icon.png  iOS / Safari 加入書籤用（180x180）
  og-image.png          社群分享預覽（1200x630）

  重新產生：
      python tools\make_icon.py

  設計：品牌藍漸層圓角方塊 + 白色對話框（浮動卡片）+ 翻譯雙箭頭。
  32px 以下自動改用簡化的單箭頭版本，確保小尺寸仍可辨識。

── 手動放置 ──

  demo.gif              30 秒動態展示（最能提升說服力）
  screenshot-1.png      主畫面截圖（卡片運作中）
  screenshot-2.png      設定視窗截圖

── 既有 ──

  twqr-donate.jpg       TWQR 台灣Pay 收款碼（已套用於贊助區）
  logo-draft.svg        網站 logo 草稿（尚未完成、尚未套用）
