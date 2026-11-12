import os
import json
import shutil
import logging
from scraper import YTMScraper
from downloader import AudioDownloader
from processor import AudioProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def load_config():
    config_file = "config.json"
    if not os.path.exists(config_file):
        config_file = "config.example.json"
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def run():
    print("=" * 60)
    print("Starting 'ytm-ios-alarm' Pipeline")
    print("=" * 60)

    config = load_config()
    top_n = config.get("top_songs_count", 7)
    duration = config.get("snippet_duration_seconds", 30)
    output_dir = config.get("output_dir", "./output")
    icloud_dir = config.get("icloud_sync_dir", "")
    auth_file = config.get("auth_file", "oauth.json")

    os.makedirs(output_dir, exist_ok=True)

    # 1. Fetch Top Songs
    scraper = YTMScraper(auth_file=auth_file)
    top_songs = scraper.get_top_songs(limit=top_n)

    if not top_songs:
        logging.warning("No top songs could be retrieved. Checking fallback URLs...")
        fallbacks = config.get("fallback_songs", [])
        for idx, url in enumerate(fallbacks):
            top_songs.append({
                "title": f"Fallback Track {idx + 1}",
                "artist": "Various",
                "video_id": f"fallback_{idx}",
                "url": url
            })

    if not top_songs:
        logging.error("No songs available to process. Exiting.")
        return

    print(f"\n[Found {len(top_songs)} Candidate Songs]:")
    for i, s in enumerate(top_songs, 1):
        print(f"  {i}. {s['title']} - {s['artist']}")

    # 2. Pick the #1 Most Listened-To Song (or primary target)
    target_song = top_songs[0]
    print(f"\n[Selecting Top Track]: {target_song['title']} ({target_song['url']})")

    # 3. Download Audio
    delay_sec = config.get("download_delay_seconds", 3)
    downloader = AudioDownloader(download_dir="./downloads", delay_seconds=delay_sec)
    raw_audio_path = downloader.download_track(target_song['url'], output_name="target_track")

    if not raw_audio_path or not os.path.exists(raw_audio_path):
        logging.error("Failed to download audio file.")
        return

    # 4. Extract Peak 30s Snippet & Convert for iOS
    processor = AudioProcessor(
        snippet_duration_sec=duration,
        fade_in_ms=config.get("fade_in_ms", 1000),
        fade_out_ms=config.get("fade_out_ms", 1500)
    )

    final_alarm_file = os.path.join(output_dir, "alarm.m4a")
    snippet_path = processor.extract_snippet(raw_audio_path, final_alarm_file)

    if not snippet_path:
        logging.error("Failed to generate alarm snippet.")
        return

    print(f"\n✅ Successfully generated alarm snippet: {final_alarm_file}")

    # 5. Sync to iCloud Drive if path exists
    if icloud_dir and os.path.exists(icloud_dir):
        dest_path = os.path.join(icloud_dir, "alarm.m4a")
        shutil.copyfile(final_alarm_file, dest_path)
        print(f"☁️ Synced to iCloud Shortcuts directory: {dest_path}")
    else:
        print(f"ℹ️ iCloud directory '{icloud_dir}' not detected or not configured yet.")
        print(f"   You can manually copy '{final_alarm_file}' to your iPhone via iCloud Drive, AirDrop, or Telegram/Drive.")

    print("\n'ytm-ios-alarm' pipeline finished successfully.")

if __name__ == "__main__":
    run()
