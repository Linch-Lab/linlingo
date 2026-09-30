# LinLingo v1.0.2

**品牌更名：PopLingo → LinLingo**

## 為什麼更名

「PopLingo」已被兩個同類翻譯產品使用：

- **PopLingo: Popup Dictionary** — Google Play 上的系統級日文辭典覆蓋層
- **Poplingo - AI 翻译 & 沉浸阅读** — Chrome / Edge 的 AI 翻譯擴充

兩者同屬翻譯軟體，為避免商標混淆與搜尋結果被蓋掉，
在正式對外推廣前更名為 **LinLingo**。

## 既有使用者請注意

**你不需要重新設定。** 首次啟動 v1.0.2 時，程式會自動把設定從

```
%APPDATA%\PopLingo\config.json
```

搬移到

```
%APPDATA%\LinLingo\config.json
```

API Key、語言、翻譯風格、卡片外觀等所有偏好都會保留。

舊的 `PopLingo.exe` 可以直接刪除。

## 功能面

本版**沒有功能變更**，與 v1.0.1 完全相同。

## 檔案

| 檔案 | 說明 |
|---|---|
| `LinLingo-win64.zip` | 免安裝版，解壓後執行 `LinLingo.exe` |
| `SHA256SUMS.txt` | 檔案雜湊值 |

驗證方式：

```bat
certutil -hashfile LinLingo-win64.zip SHA256
```

## 連結

- 官網：https://linlingo.billlinch.com/
- 下載：https://linlingo.billlinch.com/download.html
- 原始碼：https://github.com/Linch-Lab/linlingo

## 授權

MIT License
