import os
import sys
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
    delay_sec = config.get("download_delay_seconds", 3)
    playlist_id = os.environ.get("YTM_PLAYLIST_ID") or config.get("playlist_id", "")

    os.makedirs(output_dir, exist_ok=True)

    # 1. Fetch Top Songs
    scraper = YTMScraper(auth_file=auth_file)
    top_songs = scraper.get_top_songs(limit=top_n, playlist_id=playlist_id)

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
        sys.exit(1)

    print(f"\n[Found {len(top_songs)} Candidate Songs]:")
    for i, s in enumerate(top_songs, 1):
        print(f"  {i}. {s['title']} - {s['artist']}")

    # 2. Resilient Track Processing Loop
    downloader = AudioDownloader(download_dir="./downloads", delay_seconds=delay_sec)
    processor = AudioProcessor(
        snippet_duration_sec=duration,
        fade_in_ms=config.get("fade_in_ms", 1000),
        fade_out_ms=config.get("fade_out_ms", 1500)
    )

    final_alarm_file = os.path.join(output_dir, "alarm.m4a")
    success = False

    for idx, target_song in enumerate(top_songs, 1):
        print(f"\n[Attempting Track {idx}/{len(top_songs)}]: {target_song['title']} ({target_song['url']})")
        
        raw_audio_path = downloader.download_track(target_song['url'], output_name=f"track_candidate_{idx}")
        if not raw_audio_path or not os.path.exists(raw_audio_path):
            logging.warning(f"Download failed for '{target_song['title']}'. Trying next candidate...")
            continue

        snippet_path = processor.extract_snippet(raw_audio_path, final_alarm_file)
        if not snippet_path:
            logging.warning(f"Audio snippet extraction failed for '{target_song['title']}'. Trying next candidate...")
            continue

        print(f"\n✅ Successfully generated alarm snippet from: {target_song['title']}")
        success = True
        break

    if not success:
        logging.error("All candidate tracks failed processing.")
        sys.exit(1)

    # 3. Sync to iCloud Drive if path exists
    if icloud_dir and os.path.exists(icloud_dir):
        dest_path = os.path.join(icloud_dir, "alarm.m4a")
        shutil.copyfile(final_alarm_file, dest_path)
        print(f"☁️ Synced to iCloud Shortcuts directory: {dest_path}")
    else:
        print(f"ℹ️ iCloud directory '{icloud_dir}' not detected or not configured.")
        print(f"   Exported alarm artifact ready at: {final_alarm_file}")

    print("\n'ytm-ios-alarm' pipeline finished successfully.")

if __name__ == "__main__":
    run()
