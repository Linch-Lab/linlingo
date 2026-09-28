@echo off
setlocal
cd /d "%~dp0"

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
if exist "config.json" (
    findstr /C:"api_key" "config.json" >nul 2>nul
    if %errorlevel%==0 (
        echo [INFO] config.json contains api_key.
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

git commit -m "PopLingo v1.0.0"
git remote remove origin >nul 2>nul
git remote add origin "%REPO%"
git push -u origin main

echo.
echo ==============================
echo   [OK] Pushed to %REPO%
echo ==============================
echo.
echo To publish a release (auto-builds the EXE on GitHub):
echo     git tag v1.0.0
echo     git push origin v1.0.0
echo.
echo Remember to update GITHUB_REPO in app.py and the URL in latest.json.
pause
