@echo off
rem ============================================================
rem  PopLingo publish helper
rem  This file lives in app\ but operates on the repository root
rem  (one level up). Normally you can just use git directly.
rem
rem  IMPORTANT: keep this file pure ASCII.
rem  cmd.exe reads .bat files using the system ANSI codepage; multi-byte
rem  comments corrupt its byte-offset tracking and make it misread lines.
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

if not "%REPO%"=="" (
    git remote remove origin >nul 2>nul
    git remote add origin "%REPO%"
)
git push

echo.
echo ==============================
echo   [OK] Pushed.
echo ==============================
echo.
echo To publish a release (CI builds the EXE and creates the Release):
echo     git tag v1.0.1
echo     git push origin v1.0.1
pause
