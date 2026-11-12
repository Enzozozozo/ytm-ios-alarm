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

## ⚡ Quick Ways to Try

### Option 1: 1-Click Cloud Automation (Zero Installation)
Anyone can use this without installing Python or FFmpeg:
1. **Fork this repository** to your GitHub account.
2. In YouTube Music, create an **Unlisted** playlist with your favorite alarm songs and copy the link.
3. In your forked repository: go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab.
4. Add variable:
   * **Name**: `YTM_PLAYLIST_ID`
   * **Value**: Your playlist URL or ID.
5. Go to the **Actions** tab and click **Run workflow**. Your daily alarm snippet will automatically be built and published to:
   ```text
   https://github.com/<YOUR_USERNAME>/ytm-ios-alarm/releases/latest/download/alarm.m4a
   ```

---

### Option 2: Install as a Python CLI Tool
Install directly from GitHub into any Python environment:

```bash
pip install git+https://github.com/Enzozozozo/ytm-ios-alarm.git
```
*(Requires `ffmpeg` installed on your machine).*

Run from anywhere in your terminal:
```bash
# Generate 30s chorus from an unlisted/public playlist
ytm-ios-alarm --playlist "https://music.youtube.com/playlist?list=PL..."

# Customize duration and output location
ytm-ios-alarm --playlist "PL..." --duration 45 --output-dir ~/Desktop
```

---

### Option 3: Run with Docker
No local Python or FFmpeg installation needed:

```bash
docker run --rm \
  -e YTM_PLAYLIST_ID="https://music.youtube.com/playlist?list=PL..." \
  -v $(pwd)/output:/app/output \
  ghcr.io/enzozozozo/ytm-ios-alarm:latest
```

---

## 🛠️ Local Development & Advanced Setup

---

## ☁️ Running 100% Cloud-Native (GitHub Actions)

If you want the entire process to run automatically with **all your personal computers powered off** and **zero risk to your Google account**:

### 1. Create an Unlisted YouTube Music Playlist
1. Open [music.youtube.com](https://music.youtube.com) or the YouTube Music app on your phone.
2. Create a new playlist called **"Alarm Songs"** and set its privacy to **Unlisted**.
3. Add a few songs you like to it.
4. Copy the playlist URL or Playlist ID from the share button (e.g. `https://music.youtube.com/playlist?list=PL...` or `PL...`).

### 2. Configure Your GitHub Repository
1. In your GitHub repository:
   * Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab (or **Secrets** tab).
   * Click **New repository variable** (or secret).
   * **Name**: `YTM_PLAYLIST_ID`
   * **Value**: Paste your playlist URL or ID.
   * Click **Add variable**.
*(Because the playlist is unlisted, the GitHub runner queries it completely anonymously. No Google account login, session cookies, or passwords are used!)*

### 3. Automated Release & Direct iPhone Download
The workflow [`.github/workflows/generate-alarm.yml`](.github/workflows/generate-alarm.yml) runs every day at 21:00 UTC (or on-demand via **Run workflow**):
- Fetches the most recently added songs from your unlisted playlist.
- Downloads the audio track on GitHub's cloud servers.
- Trims the 30s peak chorus using `ffmpeg`.
- Publishes the file to a permanent GitHub Release under tag `latest`.

#### Direct iPhone Shortcuts Action:
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
