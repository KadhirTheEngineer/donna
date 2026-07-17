@echo off
"%~dp0..\.venv\Scripts\python.exe" "%~dp0migrate.py"
exit /b %ERRORLEVEL%
