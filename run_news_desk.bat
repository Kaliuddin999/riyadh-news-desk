@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" fetch_news.py %*
echo Exit code: %ERRORLEVEL%
pause
