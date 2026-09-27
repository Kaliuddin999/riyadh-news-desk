RIYADH NEWS DESK

Page:      https://kaliuddin999.github.io/riyadh-news-desk/
Password:  in secret\password.txt (never share, never commit)

Run once by hand:      run_news_desk.bat
Preview (no upload):   run_news_desk.bat --dry-run
Check feeds:           .venv\Scripts\python.exe check_feeds.py
Log:                   logs\run.log
Hourly job:            Task Scheduler > RiyadhNewsDesk  (re-create: powershell -ExecutionPolicy Bypass -File setup_task.ps1)

Change password: edit secret\password.txt, run run_news_desk.bat once.
Every device will then ask for the new password.

Shalfa (9613) news keeps 1 year; other news 14 days.
