import os
import time
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AudioDownloader:
    def __init__(self, download_dir: str = "./downloads", delay_seconds: int = 3):
        self.download_dir = download_dir
        self.delay_seconds = delay_seconds
        os.makedirs(self.download_dir, exist_ok=True)

    def download_track(self, video_url: str, output_name: str) -> Optional[str]:
        """
        Downloads only the audio stream of a YouTube / YouTube Music track,
        with a rate-limiting delay to avoid bot detection.
        Returns the path to the downloaded audio file.
        """
        output_template = os.path.join(self.download_dir, f"{output_name}.%(ext)s")
        
        if self.delay_seconds > 0:
            logging.info(f"Pausing for {self.delay_seconds}s before fetching audio...")
            time.sleep(self.delay_seconds)
        
        try:
            import yt_dlp
            ydl_opts = {
                'format': 'bestaudio/best',  # Highest quality audio stream available
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'noplaylist': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                # In case yt-dlp converts or updates the ext
                base, _ = os.path.splitext(downloaded_file)
                for ext in ['.m4a', '.webm', '.opus', '.mp3']:
                    candidate = base + ext
                    if os.path.exists(candidate):
                        return candidate
                if os.path.exists(downloaded_file):
                    return downloaded_file
        except ImportError:
            logging.error("yt-dlp is not installed. Run 'pip install yt-dlp'")
        except Exception as e:
            logging.error(f"Failed to download audio for {video_url}: {e}")
            
        return None
