import os
import sys
import json
import shutil
import logging
import argparse

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from scraper import YTMScraper
from downloader import AudioDownloader
from processor import AudioProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def parse_args():
    parser = argparse.ArgumentParser(
        prog="ytm-ios-alarm",
        description="Extracts peak energetic chorus snippets from YouTube Music into iOS alarms."
    )
    parser.add_argument("-p", "--playlist", help="YouTube Music unlisted or public playlist URL/ID")
    parser.add_argument("-d", "--duration", type=int, help="Snippet duration in seconds (default: 15)")
    parser.add_argument("-o", "--output-dir", help="Directory where alarm.m4a is saved (default: ./output)")
    parser.add_argument("-c", "--config", help="Custom config.json path")
    parser.add_argument("-n", "--limit", type=int, help="Max candidate songs to evaluate (default: 7)")
    parser.add_argument("-t", "--github-token", help="GitHub Personal Access Token to upload alarm.m4a to Releases")
    parser.add_argument("--github-repo", help="Target GitHub repository (e.g. Enzozozozo/ytm-ios-alarm)")
    return parser.parse_args()

def upload_to_github_release(file_path: str, repo: str, token: str, tag: str = "latest") -> bool:
    """Uploads the generated alarm.m4a directly to GitHub Releases under tag 'latest'."""
    import urllib.request
    import urllib.error

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ytm-ios-alarm"
    }

    # 1. Get or create the release for tag
    release_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    release_data = None
    try:
        req = urllib.request.Request(release_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            release_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Create release
            create_url = f"https://api.github.com/repos/{repo}/releases"
            payload = json.dumps({
                "tag_name": tag,
                "name": "Latest Daily Alarm",
                "body": "Automated alarm snippet generated from playlist.",
                "draft": False,
                "prerelease": False
            }).encode()
            req = urllib.request.Request(create_url, data=payload, headers={**headers, "Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                release_data = json.loads(resp.read().decode())
        else:
            logging.error(f"GitHub API error fetching release: {e}")
            return False

    if not release_data or "id" not in release_data:
        logging.error("Failed to retrieve or create GitHub release.")
        return False

    # 2. Check if asset already exists and delete it
    file_name = os.path.basename(file_path)
    for asset in release_data.get("assets", []):
        if asset.get("name") == file_name:
            delete_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset['id']}"
            del_req = urllib.request.Request(delete_url, headers=headers, method="DELETE")
            try:
                with urllib.request.urlopen(del_req):
                    logging.info(f"Deleted previous release asset '{file_name}'")
            except Exception as e:
                logging.warning(f"Could not delete old asset: {e}")

    # 3. Upload new asset
    upload_url = release_data.get("upload_url", "").split("{")[0]
    upload_url = f"{upload_url}?name={file_name}"
    
    with open(file_path, "rb") as f:
        data = f.read()

    upload_headers = {
        **headers,
        "Content-Type": "audio/mp4",
        "Content-Length": str(len(data))
    }

    req = urllib.request.Request(upload_url, data=data, headers=upload_headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"\n🚀 Successfully uploaded {file_name} to GitHub Release!")
            print(f"👉 Direct download link for iPhone: https://github.com/{repo}/releases/latest/download/{file_name}")
            return True
    except Exception as e:
        logging.error(f"Failed to upload asset to GitHub Release: {e}")
        return False

def load_config(config_path=None):
    config_file = config_path or "config.json"
    if not os.path.exists(config_file):
        config_file = "config.example.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run(args=None):
    if args is None:
        args = parse_args()

    print("=" * 60)
    print("Starting 'ytm-ios-alarm' Pipeline")
    print("=" * 60)

    config = load_config(args.config)
    top_n = args.limit or config.get("top_songs_count", 7)
    duration = args.duration or config.get("snippet_duration_seconds", 15)
    output_dir = args.output_dir or config.get("output_dir", "./output")
    icloud_dir = config.get("icloud_sync_dir", "")
    delay_sec = config.get("download_delay_seconds", 3)
    playlist_id = args.playlist or os.environ.get("YTM_PLAYLIST_ID") or config.get("playlist_id", "")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN") or config.get("github_token", "")
    github_repo = args.github_repo or os.environ.get("GITHUB_REPOSITORY") or config.get("github_repo", "Enzozozozo/ytm-ios-alarm")

    os.makedirs(output_dir, exist_ok=True)

    # 1. Fetch Top Songs
    scraper = YTMScraper()
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

    # 2. Daily shuffle: Deterministic pseudorandom daily shuffle based on today's calendar date
    # Ensures a fresh random track each day while being idempotent across runs on the same date.
    import datetime
    import random
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    rng = random.Random(today_str)
    ordered_candidates = list(top_songs)
    rng.shuffle(ordered_candidates)
    print(f"\n[Today's Daily Shuffle Selection ({today_str})]: {ordered_candidates[0]['title']}")

    # 3. Resilient Track Processing Loop
    downloader = AudioDownloader(download_dir="./downloads", delay_seconds=delay_sec)
    processor = AudioProcessor(
        snippet_duration_sec=duration,
        fade_in_ms=config.get("fade_in_ms", 1000),
        fade_out_ms=config.get("fade_out_ms", 1000)
    )

    final_alarm_file = os.path.join(output_dir, "alarm.m4a")
    success = False

    for idx, target_song in enumerate(ordered_candidates, 1):
        print(f"\n[Attempting Track {idx}/{len(ordered_candidates)}]: {target_song['title']} ({target_song['url']})")
        
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

    # 4. Upload to GitHub Releases if token is provided
    if github_token:
        print(f"\n☁️ Uploading alarm snippet to GitHub Release ({github_repo})...")
        upload_to_github_release(final_alarm_file, github_repo, github_token, tag="latest")

    # 5. Sync to iCloud Drive if path exists
    if icloud_dir and os.path.exists(icloud_dir):
        dest_path = os.path.join(icloud_dir, "alarm.m4a")
        shutil.copyfile(final_alarm_file, dest_path)
        print(f"☁️ Synced to iCloud Shortcuts directory: {dest_path}")
    else:
        print(f"ℹ️ iCloud directory '{icloud_dir}' not detected or not configured.")
        print(f"   Exported alarm artifact ready at: {final_alarm_file}")

    print("\n'ytm-ios-alarm' pipeline finished successfully.")

def main():
    run()

if __name__ == "__main__":
    main()
