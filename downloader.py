import os
import time
import logging
from typing import Optional
import yt_dlp

logger = logging.getLogger(__name__)

def download_audio(
    video_url: str,
    output_name: str,
    download_dir: str = "./downloads",
    delay_seconds: int = 0
) -> Optional[str]:
    os.makedirs(download_dir, exist_ok=True)

    # Purge stale files with this candidate prefix to prevent cache poisoning
    for ext in ('.m4a', '.webm', '.opus', '.mp3', '.part'):
        stale_file = os.path.join(download_dir, f"{output_name}{ext}")
        if os.path.exists(stale_file):
            try:
                os.remove(stale_file)
            except OSError:
                pass

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    output_template = os.path.join(download_dir, f"{output_name}.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if not info:
                return None
            downloaded_file = ydl.prepare_filename(info)
            base, _ = os.path.splitext(downloaded_file)
            for ext in ('.m4a', '.webm', '.opus', '.mp3'):
                candidate = base + ext
                if os.path.exists(candidate):
                    return candidate
            if os.path.exists(downloaded_file):
                return downloaded_file
    except Exception as e:
        logger.error(f"Download failed for {video_url}: {e}")

    return None
