# Setup Instructions for a New PC 💻⏰

This guide walks you through setting up `ytm-ios-alarm` on another Windows PC in under 3 minutes.

---

## 1. Prerequisites

### Step 1.1: Install Python (if not installed)
1. Download Python 3.12+ from [python.org](https://www.python.org/downloads/).
2. **Crucial:** On the first installer screen, check the box:
   ☑️ **"Add python.exe to PATH"**.

### Step 1.2: Install FFmpeg
Open **PowerShell** as Administrator or normal user and run:
```powershell
winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
```

---

## 2. Clone the Repository & Install Dependencies

Open **PowerShell** and run:

```powershell
# 1. Clone repository
git clone https://github.com/Enzozozozo/ytm-ios-alarm.git
cd ytm-ios-alarm

# 2. Create Python virtual environment
python -m venv .venv

# 3. Install required packages
.\.venv\Scripts\pip install -r requirements.txt
```

---

## 3. Configure `config.json`

Create a file named `config.json` in the root folder (or copy your existing one):

```json
{
  "top_songs_count": 50,
  "snippet_duration_seconds": 15,
  "fade_in_ms": 1000,
  "fade_out_ms": 1000,
  "output_dir": "./output",
  "icloud_sync_dir": "",
  "playlist_id": "https://www.youtube.com/watch?v=_Ca0cqCrntY&list=PLGbYM1ZrkDKY",
  "github_repo": "Enzozozozo/ytm-ios-alarm",
  "github_token": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN",
  "download_delay_seconds": 3,
  "fallback_songs": []
}
```
*(Make sure to put your real GitHub token in `"github_token"`).*

---

## 4. Test Manual Run

Double-click:
👉 **`run_manual.bat`**

Or in PowerShell:
```powershell
.\.venv\Scripts\python.exe main.py --force
```
You should see:
```text
[INFO] Loaded 9 tracks. Today's pick: ...
[INFO] Peak window: ...s - ...s (-X.X dBFS)
[INFO] Uploaded alarm.m4a -> ...
[INFO] Uploaded daily.m4a -> ...
```

---

## 5. Register the Automatic Windows Startup Task

Run this **one command** in **PowerShell** from inside the `ytm-ios-alarm` folder:

```powershell
$projectDir = (Get-Location).Path
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$projectDir\run_silent.vbs`"" -WorkingDirectory $projectDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "YTM_iOS_Daily_Alarm" -Action $action -Trigger $trigger -Settings $settings -Description "Daily YouTube Music iOS Alarm generator on logon" -Force
```

### What this does:
* Fires silently in the background **only when you turn your PC on and log in**.
* Automatically detects if today's alarm has already been run; if so, exits in 0.05 seconds with zero downloads or CPU usage.
* Zero popup windows.

---

## 6. iPhone Shortcut Setup (If not already set up)

In the iOS **Shortcuts** app:

1. Create a shortcut named **"Play Daily Alarm"**:
   - Action 1: **Get Contents of URL** ➔ `https://github.com/Enzozozozo/ytm-ios-alarm/releases/latest/download/daily.m4a`
   - Action 2: **Play Sound**
2. In the **Automation** tab:
   - Trigger: **When Alarm Goes Off** or **Time of Day** (e.g. 7:00 AM).
   - Set: **Run Immediately** (checked).
   - Set: **Notify When Run** (OFF).
   - Action: **Run Shortcut** ➔ `Play Daily Alarm`.
