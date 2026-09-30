@echo off
rem ============================================================
rem  LinLingo environment diagnostic
rem  Run this if the program will not start, then report the output.
rem
rem  IMPORTANT: keep this file pure ASCII.
rem  cmd.exe reads .bat files using the system ANSI codepage (CP950
rem  on a Traditional Chinese system). Multi-byte comments corrupt its
rem  byte-offset tracking and make it misread EARLIER lines.
rem ============================================================
cd /d "%~dp0"

echo ============================================================
echo   LinLingo environment check
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
for %%F in (app.py run.bat LinLingo.vbs version.txt) do (
  if exist "%%F" (echo    OK      %%F) else (echo    MISSING %%F)
)
echo.

echo [3] Config / logs
echo ----------------------------------------
if exist "%APPDATA%\LinLingo\config.json" (
  echo    config : %APPDATA%\LinLingo\config.json
) else (
  echo    config : not created yet
)
if exist "%APPDATA%\LinLingo\launcher.log" (
  echo    launcher.log contents:
  type "%APPDATA%\LinLingo\launcher.log"
) else (
  echo    launcher.log : none
)
if exist "%APPDATA%\LinLingo\linlingo.log" (
  echo    linlingo.log tail:
  powershell -NoProfile -Command "Get-Content -Encoding UTF8 '%APPDATA%\LinLingo\linlingo.log' -Tail 20"
) else (
  echo    linlingo.log : none
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
