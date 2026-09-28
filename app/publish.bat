@echo off
rem ============================================================
rem  PopLingo publish helper
rem  本檔位於 app\ ，實際操作的是「上一層」的倉庫根目錄。
rem  日常推送其實只要用 git 指令即可，本檔是給不熟悉 git 的人用的。
rem ============================================================
setlocal
cd /d "%~dp0.."

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] git not found.
    echo Install Git for Windows: https://git-scm.com/download/win
    pause
    exit /b 1
)

if "%~1"=="" (
    set /p REPO="Enter GitHub repo URL (e.g. https://github.com/you/poplingo.git): "
) else (
    set "REPO=%~1"
)

echo.
echo === Safety check ===
if exist "app\config.json" (
    findstr /C:"api_key" "app\config.json" >nul 2>nul
    if %errorlevel%==0 (
        echo [INFO] app\config.json contains api_key.
        echo        It is listed in .gitignore and must NOT be pushed.
    )
)

if not exist ".git" (
    echo Initializing git repository...
    git init
    git branch -M main
)

git add -A
echo.
echo === Files to be committed ===
git status --short
echo.

set /p OK="Commit and push? (y/n): "
if /i not "%OK%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

set /p MSG="Commit message: "
if "%MSG%"=="" set "MSG=update"

git commit -m "%MSG%"
if "%REPO%"=="" goto after_push
git remote remove origin >nul 2>nul
git remote add origin "%REPO%"
git push -u origin main
goto after_push

:after_push
git push
echo.
echo ==============================
echo   [OK] Pushed.
echo ==============================
echo.
echo To publish a release (auto-builds the EXE on GitHub):
echo     git tag v1.0.0
echo     git push origin v1.0.0
pause
