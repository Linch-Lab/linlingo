# LinLingo v1.0.1

修正 PowerPoint 相容性問題，並補上應用程式內的官網連結。

## 修正

### PowerPoint 中 `Ctrl+Enter` 無法回填

原本 `Ctrl+Enter` 是**卡片視窗的按鍵綁定**，只有在卡片有焦點時才生效。
回填時程式會把前景交給目標程式，而 Windows 對前景轉換有鎖，
搶回焦點不一定成功 —— 焦點一旦留在 PowerPoint，
之後按的 `Ctrl+Enter` 就由 PowerPoint 處理，觸發它自己的快速鍵
（切換版面配置／新增投影片），把輸入打断。

另外，回填送出 `Ctrl+V` 後**立刻**把焦點拉回卡片，
對 PowerPoint 這類較重的程式可能來不及完成貼上。

**修正內容**

- 新增全域熱鍵 `Ctrl+Alt+Enter`：焦點在任何程式都能直接插入譯文
- 回填後改為**延後 180ms** 再收回焦點，讓目標程式完成貼上
- 加入 350ms 去重鎖，避免兩組熱鍵同時觸發

## 新增

- 應用程式內的官網連結：
  - 說明視窗底部：「使用說明 / 翻譯引擎教學 / 常見問題 / 問題回報」
  - 設定頁的「不知道怎麼填？看圖文教學 →」
- 設定檔新增 `commit_global_vk` / `commit_global_mods`

## 目前的全域熱鍵

| 熱鍵 | 功能 |
|---|---|
| `Ctrl+Alt+T` | 開關翻譯模式 |
| `Ctrl+Alt+C` | 把焦點拉回卡片 |
| `Ctrl+Alt+Enter` | 隨處插入譯文 |

## 檔案

| 檔案 | 說明 |
|---|---|
| `LinLingo-win64.zip` | 免安裝版，解壓後執行 `LinLingo.exe` |
| `SHA256SUMS.txt` | 檔案雜湊值 |

下載：https://linlingo.billlinch.com/download.html

## 授權

MIT License
