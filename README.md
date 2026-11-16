# ytm-ios-alarm ⏰🎵

Automated CI/CD audio pipeline that fetches your tracks on YouTube Music, deterministically shuffles them daily, extracts the peak 15-second section with highest mean dB (loudest RMS energy window), formats it as an iOS-compatible audio alarm (`alarm.m4a`), and delivers it directly to Apple Shortcuts via GitHub Releases or iCloud Drive.

---

## 🛠️ Pipeline Architecture

```
[YouTube Music]
       │
       ▼ (1. Fetch Playlist Tracks via yt-dlp)
[Metadata Extractor: track titles, video IDs]
       │
       ▼ (2. Daily Shuffle: Deterministic calendar shuffle)
[Select primary track of the day]
       │
       ▼ (3. Audio Downloader: yt-dlp)
[Raw Track Audio (.m4a / .opus)]
       │
       ▼ (4. Snippet Locator & Trimmer: ffmpeg / pydub)
[Detect loudest/highest mean dB 15s chorus window]
       │
       ▼ (5. iOS Exporter)
[alarm.m4a with cross-fade]
       │
       ▼ (6. Cloud Sync)
[GitHub Releases / iCloud Drive / Shortcuts]
       │
       ▼ (7. Native iOS Automation)
[iPhone: Shortcuts Automation pulls and plays alarm at scheduled time]
```

---

## ⚡ Quick Setup

See [`SETUP_NEW_PC.md`](SETUP_NEW_PC.md) for the full Windows Task Scheduler + iPhone Shortcuts setup guide.

### Install as a Python CLI Tool
Install directly from GitHub into any Python environment:

```bash
pip install git+https://github.com/Enzozozozo/ytm-ios-alarm.git
```
*(Requires `ffmpeg` installed on your machine).*

Run from anywhere in your terminal:
```bash
# Generate 15s chorus from an unlisted/public playlist
ytm-ios-alarm --playlist "https://music.youtube.com/playlist?list=PL..."

# Customize duration and output location
ytm-ios-alarm --playlist "PL..." --duration 15 --output-dir ~/Desktop
```

---

## 📱 iPhone Shortcuts Setup (One-time, 2 minutes)

1. Open the **Shortcuts** app on your iPhone and create a shortcut named **"Play Daily Alarm"**:
   * **Get Contents of URL** → `https://github.com/Enzozozozo/ytm-ios-alarm/releases/latest/download/daily.m4a`
   * **Play Sound** → `[Contents of URL]`
2. Open the **Automation** tab → **+ (New Automation)**.
3. Select **Alarm** (e.g. "When any alarm goes off") or **Time of Day** (e.g. "At 7:00 AM").
4. Choose **Run Immediately** and turn **Notify When Run** OFF.
5. Add action: **Run Shortcut** → **Play Daily Alarm**.
