import os
import sys
import json
import shutil
import random
import logging
import argparse
import datetime
from typing import Dict, Any

from models import Track
from scraper import fetch_tracks
from downloader import download_audio
from processor import create_alarm_snippet
from publisher import upload_to_github_release

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ytm-ios-alarm")

def parse_args():
    parser = argparse.ArgumentParser(
        prog="ytm-ios-alarm",
        description="Extracts peak energetic chorus snippets from YouTube Music into iOS alarms."
    )
    parser.add_argument("-p", "--playlist", help="YouTube Music unlisted or public playlist URL/ID")
    parser.add_argument("-d", "--duration", type=int, help="Snippet duration in seconds (default: 15)")
    parser.add_argument("-o", "--output-dir", help="Directory where alarm.m4a is saved (default: ./output)")
    parser.add_argument("-c", "--config", help="Custom config.json path")
    parser.add_argument("-n", "--limit", type=int, help="Max candidate songs to evaluate (default: 50)")
    parser.add_argument("-t", "--github-token", help="GitHub Personal Access Token to upload to Releases")
    parser.add_argument("--github-repo", help="Target GitHub repository (e.g. Enzozozozo/ytm-ios-alarm)")
    parser.add_argument("-f", "--force", action="store_true", help="Force update even if already run today")
    return parser.parse_args()

def load_config(config_path: str = None) -> Dict[str, Any]:
    config_file = config_path or "config.json"
    if not os.path.exists(config_file):
        config_file = "config.example.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run(args=None) -> int:
    if args is None:
        args = parse_args()

    config = load_config(args.config)
    limit = args.limit or config.get("top_songs_count", 50)
    duration = args.duration or config.get("snippet_duration_seconds", 15)
    output_dir = args.output_dir or config.get("output_dir", "./output")
    icloud_dir = config.get("icloud_sync_dir", "")
    delay_sec = config.get("download_delay_seconds", 3)
    playlist_id = args.playlist or os.environ.get("YTM_PLAYLIST_ID") or config.get("playlist_id", "")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN") or config.get("github_token", "")
    github_repo = args.github_repo or os.environ.get("GITHUB_REPOSITORY") or config.get("github_repo", "Enzozozozo/ytm-ios-alarm")

    os.makedirs(output_dir, exist_ok=True)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    state_file = os.path.join(output_dir, ".last_run")
    if not getattr(args, "force", False) and os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                if f.read().strip() == today_str:
                    logger.info(f"Already updated for today ({today_str}). Skipping.")
                    return 0
        except OSError:
            pass

    tracks = fetch_tracks(playlist_id, limit=limit)

    if not tracks:
        fallbacks = config.get("fallback_songs", [])
        for idx, url in enumerate(fallbacks):
            tracks.append(Track(
                title=f"Fallback Track {idx + 1}",
                artist="Various",
                video_id=f"fallback_{idx}",
                url=url
            ))

    if not tracks:
        logger.error("No songs available to process.")
        return 1

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    rng = random.Random(today_str)
    ordered_tracks = list(tracks)
    rng.shuffle(ordered_tracks)
    logger.info(f"Loaded {len(tracks)} tracks. Today's pick: {ordered_tracks[0].title}")

    final_alarm_file = os.path.join(output_dir, "alarm.m4a")
    fade_in_ms = config.get("fade_in_ms", 1000)
    fade_out_ms = config.get("fade_out_ms", 1000)
    downloads_dir = "./downloads"

    success = False
    for idx, target_song in enumerate(ordered_tracks, 1):
        raw_audio_path = download_audio(
            target_song.url,
            output_name=f"track_candidate_{idx}",
            download_dir=downloads_dir,
            delay_seconds=delay_sec if idx > 1 else 0
        )
        if not raw_audio_path or not os.path.exists(raw_audio_path):
            logger.warning(f"Download failed for '{target_song.title}'. Trying next candidate...")
            continue

        snippet_path = create_alarm_snippet(
            raw_audio_path,
            final_alarm_file,
            snippet_duration_sec=duration,
            fade_in_ms=fade_in_ms,
            fade_out_ms=fade_out_ms
        )

        # Cleanup raw audio to prevent unbounded disk growth
        try:
            os.remove(raw_audio_path)
        except OSError:
            pass

        if not snippet_path:
            logger.warning(f"Audio snippet extraction failed for '{target_song.title}'. Trying next candidate...")
            continue

        success = True
        break

    if not success:
        logger.error("All candidate tracks failed processing.")
        return 1

    if github_token:
        upload_to_github_release(final_alarm_file, github_repo, github_token, tag="latest")
        daily_alias = os.path.join(output_dir, "daily.m4a")
        shutil.copyfile(final_alarm_file, daily_alias)
        upload_to_github_release(daily_alias, github_repo, github_token, tag="latest")

    try:
        with open(state_file, "w", encoding="utf-8") as f:
            f.write(today_str)
    except OSError:
        pass

    if icloud_dir and os.path.exists(icloud_dir):
        try:
            dest_path = os.path.join(icloud_dir, "alarm.m4a")
            shutil.copyfile(final_alarm_file, dest_path)
            logger.info(f"Synced to iCloud: {dest_path}")
        except Exception as e:
            logger.warning(f"Could not copy to iCloud sync dir: {e}")

    return 0

def main():
    sys.exit(run())

if __name__ == "__main__":
    main()
