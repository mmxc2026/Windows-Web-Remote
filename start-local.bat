@echo off
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Startup failed. See startup-error.log for details.
echo.
pause
exit /b %RESULT%
