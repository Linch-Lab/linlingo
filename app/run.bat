@echo off
rem ============================================================
rem  LinLingo launcher - debug version (shows a console window)
rem  For everyday use double-click LinLingo.vbs instead: it
rem  starts with no window at all.
rem
rem  IMPORTANT: keep this file pure ASCII.
rem  cmd.exe reads .bat files using the system ANSI codepage (CP950
rem  on a Traditional Chinese system). Multi-byte comments corrupt its
rem  byte-offset tracking and make it misread EARLIER lines.
rem ============================================================
setlocal
cd /d "%~dp0"

set "LOGDIR=%APPDATA%\LinLingo"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>nul
set "LOG=%LOGDIR%\launcher.log"

rem 1) Prefer pythonw (no console window)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    >>"%LOG%" echo [%date% %time%] launch via pythonw
    start "" pythonw "app.py"
    exit /b 0
)

where pyw >nul 2>nul
if %errorlevel%==0 (
    >>"%LOG%" echo [%date% %time%] launch via pyw
    start "" pyw "app.py"
    exit /b 0
)

>>"%LOG%" echo [%date% %time%] pythonw not found, fallback to python

rem 2) Fall back to python (shows a console so errors are visible)
where python >nul 2>nul
if %errorlevel%==0 (
    echo [INFO] pythonw.exe not found; running with python.exe.
    echo        A console window will stay open in this mode.
    echo        For a windowless launch use LinLingo.vbs instead.
    echo.
    python app.py
    goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
    echo [INFO] pythonw.exe not found; running with py.exe.
    py app.py
    goto :end
)

echo [ERROR] Python not found. Install Python 3.8+ and check "Add Python to PATH".
echo         https://www.python.org/downloads/
pause

:end
