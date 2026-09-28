@echo off
rem ============================================================
rem  PopLingo build script
rem  Output: dist\PopLingo\PopLingo.exe  (test copy)
rem          releases\v<version>\PopLingo-win64.zip + SHA256SUMS.txt
rem
rem  IMPORTANT: keep this file pure ASCII.
rem  cmd.exe reads .bat files using the system ANSI codepage (CP950 here);
rem  multi-byte comments corrupt its byte-offset tracking and make it
rem  misread EARLIER lines (this broke the version parsing once).
rem ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.8+ and check "Add Python to PATH".
    pause
    exit /b 1
)

rem ---- read version from app.py (single source of truth) ----
set "VER="
for /f "tokens=2 delims==" %%V in ('findstr /b /c:"APP_VERSION" app.py') do set "VER=%%V"
set "VER=%VER: =%"
set VER=%VER:"=%
if "%VER%"=="" set "VER=0.0.0"

echo ==========================================
echo   PopLingo build   version %VER%
echo ==========================================
echo.

echo [1/5] Installing build tools...
python -m pip install --user --upgrade pyinstaller pystray pillow
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)

set "ICONARG="
if exist "assets\app.ico" set "ICONARG=--icon assets\app.ico"

rem Exclude heavy modules this app never uses but that PyInstaller may pull in
rem from the local environment. numpy alone adds ~27MB (19MB OpenBLAS DLL),
rem which is the main reason a local build used to be much bigger than CI.
set "EXCLUDES=--exclude-module numpy --exclude-module scipy --exclude-module pandas --exclude-module matplotlib --exclude-module yaml --exclude-module psutil --exclude-module setuptools --exclude-module pip"

echo.
echo [2/5] Building EXE (onedir, faster startup than onefile)...
python -m PyInstaller --noconfirm --onedir --windowed --name PopLingo --version-file version.txt --hidden-import pystray._win32 --collect-all pystray %EXCLUDES% %ICONARG% app.py

if not exist "dist\PopLingo\PopLingo.exe" (
    echo.
    echo [ERROR] Build failed. Check the PyInstaller output above.
    pause
    exit /b 1
)

set "OUTDIR=releases\v%VER%"
echo.
echo [3/5] Preparing %OUTDIR% ...
if not exist "releases" mkdir "releases" >nul 2>nul
if not exist "%OUTDIR%" mkdir "%OUTDIR%" >nul 2>nul

echo.
echo [4/5] Packing and hashing...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\PopLingo\*' -DestinationPath '%OUTDIR%\PopLingo-win64.zip' -Force"
powershell -NoProfile -Command "Get-FileHash '%OUTDIR%\PopLingo-win64.zip' -Algorithm SHA256 | ForEach-Object { $_.Hash + '  PopLingo-win64.zip' } | Out-File -Encoding utf8 '%OUTDIR%\SHA256SUMS.txt'"

echo.
echo [5/5] Done.
type "%OUTDIR%\SHA256SUMS.txt"
echo.
echo   Test copy : dist\PopLingo\PopLingo.exe
echo   Release   : %OUTDIR%\PopLingo-win64.zip
echo.
echo Next: git tag v%VER% ^&^& git push origin v%VER%
pause
