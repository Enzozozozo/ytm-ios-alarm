@echo off
setlocal
set PYTHONUNBUFFERED=1
where ffmpeg >nul 2>&1
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin" (
        set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin;%PATH%"
    )
)
cd /d "%~dp0"
".venv\Scripts\python.exe" -u main.py <nul >> "task_scheduler.log" 2>&1
endlocal
