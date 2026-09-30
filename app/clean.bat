@echo off
rem ============================================================
rem  LinLingo cleanup - remove build artifacts and legacy files
rem  releases\ and config are NOT touched.
rem ============================================================
cd /d "%~dp0"

echo ==========================================
echo   LinLingo cleanup
echo ==========================================
echo.
echo Will remove:
echo    build\                  PyInstaller work folder
echo    dist\                   build output (releases\ keeps the zips)
echo    *.spec                  PyInstaller spec files
echo    __pycache__             Python caches
echo    Translator.spec         legacy v0 artifact
echo.
echo Will NOT touch:
echo    releases\               official release folders
echo    app.py, docs\, config, *.md, *.bat, *.vbs
echo.
set /p OK="Continue? (y/n): "
if /i not "%OK%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Removing legacy files...
if exist "Translator.spec" del /q "Translator.spec" 2>nul
if exist "dist\Translator.exe" del /q "dist\Translator.exe" 2>nul

echo [2/5] Removing PyInstaller work folder...
if exist "build" rmdir /s /q "build" 2>nul

echo [3/5] Removing dist folder...
if exist "dist" rmdir /s /q "dist" 2>nul

echo [4/5] Removing spec files...
del /q "*.spec" 2>nul

echo [5/5] Removing __pycache__ folders...
for /d /r %%D in (__pycache__) do @if exist "%%D" rmdir /s /q "%%D" 2>nul

echo.
echo ==========================================
echo   Done. sources and releases\ are intact.
echo ==========================================
echo.
echo Next: run build.bat to produce releases\vX.Y.Z\
pause
