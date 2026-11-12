@echo off
setlocal
set PYTHONUNBUFFERED=1
set "PATH=C:\Users\tayen\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin;%PATH%"
cd /d "C:\Users\tayen\.gemini\antigravity\scratch\the-alarm-demon"
".venv\Scripts\python.exe" -u main.py >> "task_scheduler.log" 2>&1
endlocal
