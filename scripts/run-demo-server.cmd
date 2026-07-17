@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-demo-server.ps1"
exit /b %ERRORLEVEL%
