import os
import logging
import urllib.parse
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class YTMScraper:
    """
    Extracts candidate tracks from public or unlisted YouTube / YouTube Music playlists
    using yt-dlp. Completely anonymous, credential-free, and cookie-free.
    """
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def normalize_playlist_url(raw_input: str) -> str:
        """Converts raw playlist IDs or watch links into clean playlist URLs."""
        raw_input = raw_input.strip()
        if "list=" in raw_input:
            parsed = urllib.parse.urlparse(raw_input)
            params = urllib.parse.parse_qs(parsed.query)
            if "list" in params and params["list"]:
                playlist_id = params["list"][0]
                return f"https://www.youtube.com/playlist?list={playlist_id}"
        if not raw_input.startswith("http"):
            return f"https://www.youtube.com/playlist?list={raw_input}"
        return raw_input

    def get_top_songs(self, limit: int = 50, playlist_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches tracks from an unlisted or public playlist using yt-dlp.
        Returns a list of candidate track dictionaries in playlist order.
        """
        songs = []
        if not playlist_id:
            logging.warning("No playlist URL or ID provided.")
            return songs

        playlist_url = self.normalize_playlist_url(playlist_id)
        logging.info(f"Extracting candidate tracks from: {playlist_url}")

        try:
            import yt_dlp
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'noplaylist': False
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = None
                try:
                    info = ydl.extract_info(playlist_url, download=False)
                except Exception as pe:
                    # If playlist extraction fails but input contains a video link, fallback to single track
                    if "v=" in playlist_id or "youtu.be/" in playlist_id or "/watch" in playlist_id:
                        logging.warning(f"Playlist extraction failed ({pe}). Falling back to extracting single track from URL...")
                        ydl_single = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'noplaylist': True})
                        info = ydl_single.extract_info(playlist_id, download=False)
                    else:
                        raise pe

                if not info:
                    return songs

                entries = info.get('entries')
                if entries is None:
                    # Single video track
                    entries = [info]

                for entry in entries[:limit]:
                    if not entry:
                        continue
                    video_id = entry.get('id')
                    url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"
                    if not url.startswith("http"):
                        url = f"https://www.youtube.com/watch?v={url}"
                    
                    title = entry.get('title', 'Unknown Track')
                    uploader = entry.get('uploader') or entry.get('channel') or entry.get('artist') or 'Various'

                    songs.append({
                        "title": title,
                        "artist": uploader,
                        "video_id": video_id or "",
                        "url": url,
                        "duration_seconds": entry.get('duration') or 0
                    })

                logging.info(f"Loaded {len(songs)} track(s) from '{info.get('title', 'Unknown')}'")
        except Exception as e:
            logging.error(f"Failed to extract playlist: {e}")

        return songs
