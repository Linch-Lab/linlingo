# 發行版本（releases/）

每個發行版本各自一個以版本號命名的資料夾。

```
releases/
├── README.md              本文件
├── v1.0.0/
│   ├── PopLingo-win64.zip 免安裝，解壓即用
│   ├── SHA256SUMS.txt     檔案雜湊，可驗證下載完整性
│   └── RELEASE.md         版本說明與更新重點
└── v1.1.0/                （未來版本）
```

## 怎麼產生

執行 `build.bat` 會自動：

1. 從 `app.py` 讀取 `APP_VERSION`（**版本號的唯一來源**）
2. 用 PyInstaller 建置 `dist\PopLingo\PopLingo.exe`
3. 打包成 `releases\v<版本>\PopLingo-win64.zip`
4. 產生同資料夾的 `SHA256SUMS.txt`

## 中間產物 vs. 正式產物

| 位置 | 性質 | 處置 |
|---|---|---|
| `build\` | PyInstaller 工作資料夾 | 中間產物，可刪 |
| `dist\` | 建置輸出（測試用） | 中間產物，可刪 |
| `*.spec` | PyInstaller 設定 | 自動產生，可刪 |
| **`releases\`** | **正式保存的發行檔** | **保留** |

執行 `clean.bat` 會清掉前三者，**不會動到 `releases\`**。

## 發佈流程

```bat
build.bat                        :: 產生 releases\v1.0.0\
git tag v1.0.0
git push origin v1.0.0           :: GitHub Actions 自動建置並發佈 Release
```

## 版控原則

**二進位檔不進 git**，一律走 GitHub Releases。因此 `.gitignore` 排除了：

```
releases/*/PopLingo-win64/
releases/*/*.zip
releases/*/*.exe
```

實際納入版控的只有版本說明：

| 檔案 | 進版控 |
|---|---|
| `releases/README.md` | ✅ |
| `releases/v1.0.0/RELEASE.md` | ✅ |
| `releases/v1.0.0/SHA256SUMS.txt` | ✅ |
| `releases/v1.0.0/PopLingo-win64.zip` | ❌（走 Releases） |
| `releases/v1.0.0/PopLingo-win64/` | ❌（解壓後的內容） |

網站上的下載連結指向 GitHub Releases 的 `latest`，因此不需要把 zip 提交進 git。
