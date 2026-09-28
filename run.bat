@echo off
rem ============================================================
rem  PopLingo 啟動腳本（除錯用，會顯示命令列視窗）
rem  日常使用請雙擊 PopLingo.vbs —— 完全不會出現任何視窗
rem ============================================================
setlocal
cd /d "%~dp0"

set "LOGDIR=%APPDATA%\PopLingo"
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>nul
set "LOG=%LOGDIR%\launcher.log"

rem 1) 優先使用 pythonw（無命令列視窗）
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

rem 2) 找不到 pythonw 就退回 python（會顯示命令列，便於看錯誤訊息）
where python >nul 2>nul
if %errorlevel%==0 (
    echo [INFO] pythonw.exe not found; running with python.exe.
    echo        A console window will stay open in this mode.
    echo        For a windowless launch, close this and use PopLingo.vbs.
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
