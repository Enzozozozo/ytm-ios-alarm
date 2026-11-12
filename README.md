# ytm-ios-alarm ⏰🎵

Automated CI/CD audio pipeline that fetches your top listened-to tracks on YouTube Music, extracts the most energetic 30-second chorus snippet via RMS analysis, formats it as an iOS-compatible audio alarm (`alarm.m4a`), and delivers it directly to Apple Shortcuts via GitHub Releases or iCloud Drive.

---

## 🛠️ Pipeline Architecture

```
[YouTube Music]
       │
       ▼ (1. Fetch Top 7 Songs via ytmusicapi)
[Metadata Extractor: track titles, video IDs]
       │
       ▼ (2. Audio Downloader: yt-dlp)
[Raw Track Audio (.m4a / .opus)]
       │
       ▼ (3. Snippet Locator & Trimmer: ffmpeg / pydub)
[Detect loudest/highest RMS 30s chorus window]
       │
       ▼ (4. iOS Exporter)
[alarm.m4a / alarm.m4r with cross-fade]
       │
       ▼ (5. Cloud Sync)
[iCloud Drive / Shortcuts / Dropbox]
       │
       ▼ (6. Native iOS Automation)
[iPhone: Shortcuts Automation triggers alarm at scheduled time]
```

---

## 🚀 Quick Start

### 1. Requirements
Ensure Python 3.10+ is installed.
Install dependencies:
```powershell
pip install -r requirements.txt
```

You also need `ffmpeg`. If you don't have it on Windows, you can install it via Chocolatey or Winget:
```powershell
winget install Gyan.FFmpeg
# or
choco install ffmpeg
```

### 2. Configuration (`config.json`)
Copy `config.example.json` to `config.json` and adjust:
- `icloud_sync_dir`: Path to your iCloud Drive Shortcuts folder (defaults to `./output` if not using iCloud Windows app).
- `snippet_duration_sec`: 30 (default duration for an alarm snippet).
- `top_n`: 7.

### 3. YouTube Music Auth Setup
YouTube Music requires authentication to view your personal listening history and top tracks:
Run the helper:
```powershell
python auth_setup.py
```
This will guide you to paste your request headers from `music.youtube.com` into `browser_headers.txt` to generate `oauth.json`.

---

## ☁️ Running 100% Cloud-Native (GitHub Actions)

If you want the entire process to run automatically with **all your personal computers powered off**:

### 1. Push this repository to GitHub
Initialize and push this repo to your private or public GitHub account.

### 2. Add your YouTube Music Auth Secret
1. Run `python auth_setup.py` locally once to generate `oauth.json`.
2. Open `oauth.json` and copy its entire text.
3. On GitHub, go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
4. Name the secret:
   ```
   YTM_OAUTH_JSON
   ```
5. Paste the contents of `oauth.json` and click **Add secret**.

### 3. Automated Release & Direct iPhone Download
The workflow [`.github/workflows/generate-alarm.yml`](.github/workflows/generate-alarm.yml) runs every day at 21:00 UTC (or on-demand via **Run workflow**):
- Downloads your top track on GitHub's cloud servers.
- Trims the 30s peak chorus using `ffmpeg`.
- Publishes the file to a permanent GitHub Release under tag `latest`.

#### Direct iPhone Shortcuts Action (No local computer needed!):
In your iOS Shortcut automation:
1. Action: **Get Contents of URL** → `https://github.com/<YOUR_GITHUB_USERNAME>/ytm-ios-alarm/releases/latest/download/alarm.m4a`
   *(If the repo is private, add a Header: `Authorization` with value `Bearer <GITHUB_PERSONAL_ACCESS_TOKEN>`)*
2. Action: **Save File** (optional, saves to `Shortcuts/alarm.m4a` for offline playback).
3. Action: **Play Sound**.

---

## 📱 Setting Up iPhone Automation (One-time, 2 minutes)

1. Ensure the generated `alarm.m4a` is synced to your iCloud Drive inside `Shortcuts/alarm.m4a`.
2. Open the **Shortcuts** app on your iPhone.
3. Tap **Automation** at the bottom → **+ (New Automation)**.
4. Select **Alarm** (e.g. "When any alarm goes off") or **Time of Day** (e.g. "At 7:00 AM").
5. Choose **Run Immediately** (disable "Ask Before Running").
6. Add the following action chain:
   * **Get File** → Service: `iCloud Drive`, File Path: `Shortcuts/alarm.m4a`, Error If Not Found: `Yes`.
   * **Play Sound**.
7. Done! Every time Antigravity or the cron script updates `alarm.m4a`, your iPhone automatically plays the fresh snippet tomorrow morning.
