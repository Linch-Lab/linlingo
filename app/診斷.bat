@echo off
rem ============================================================
rem  PopLingo 環境診斷 —— 若程式無法啟動，請執行本檔並回報結果
rem ============================================================
cd /d "%~dp0"

echo ============================================================
echo   PopLingo environment check
echo ============================================================
echo.

echo [1] Python interpreters on PATH
echo ----------------------------------------
echo -- pythonw --
where pythonw 2>nul || echo    NOT FOUND
echo -- pyw --
where pyw 2>nul || echo    NOT FOUND
echo -- python --
where python 2>nul || echo    NOT FOUND
echo -- py --
where py 2>nul || echo    NOT FOUND
echo.

echo [2] Local files
echo ----------------------------------------
for %%F in (app.py run.bat PopLingo.vbs version.txt) do (
  if exist "%%F" (echo    OK      %%F) else (echo    MISSING %%F)
)
echo.

echo [3] Config / logs
echo ----------------------------------------
if exist "%APPDATA%\PopLingo\config.json" (
  echo    config : %APPDATA%\PopLingo\config.json
) else (
  echo    config : not created yet
)
if exist "%APPDATA%\PopLingo\launcher.log" (
  echo    launcher.log contents:
  type "%APPDATA%\PopLingo\launcher.log"
) else (
  echo    launcher.log : none
)
if exist "%APPDATA%\PopLingo\poplingo.log" (
  echo    poplingo.log tail:
  powershell -NoProfile -Command "Get-Content -Encoding UTF8 '%APPDATA%\PopLingo\poplingo.log' -Tail 20"
) else (
  echo    poplingo.log : none
)
echo.

echo [4] Windows Script Host status
echo ----------------------------------------
reg query "HKCU\Software\Microsoft\Windows Script Host\Settings" /v Enabled 2>nul || echo    HKCU: not set (default = enabled)
reg query "HKLM\Software\Microsoft\Windows Script Host\Settings" /v Enabled 2>nul || echo    HKLM: not set (default = enabled)
echo.

echo ============================================================
echo   Please copy this output back for diagnosis.
echo ============================================================
pause
