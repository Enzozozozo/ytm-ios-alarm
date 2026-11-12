import logging
import urllib.parse
from typing import List, Optional
import yt_dlp
from models import Track

logger = logging.getLogger(__name__)

def normalize_playlist_url(raw_input: str) -> str:
    raw_input = raw_input.strip()
    if "list=" in raw_input:
        parsed = urllib.parse.urlparse(raw_input)
        params = urllib.parse.parse_qs(parsed.query)
        if "list" in params and params["list"]:
            return f"https://www.youtube.com/playlist?list={params['list'][0]}"
    if not raw_input.startswith("http"):
        return f"https://www.youtube.com/playlist?list={raw_input}"
    return raw_input

def fetch_tracks(playlist_id: str, limit: int = 50) -> List[Track]:
    if not playlist_id:
        return []

    playlist_url = normalize_playlist_url(playlist_id)
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': False
    }

    tracks: List[Track] = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = None
            try:
                info = ydl.extract_info(playlist_url, download=False)
            except Exception as err:
                if any(x in playlist_id for x in ("v=", "youtu.be/", "/watch")):
                    ydl_single = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'noplaylist': True})
                    info = ydl_single.extract_info(playlist_id, download=False)
                else:
                    raise err

            if not info:
                return tracks

            raw_entries = info.get('entries')
            entries = [info] if raw_entries is None else list(raw_entries)

            for entry in entries[:limit]:
                if not entry:
                    continue
                video_id = entry.get('id', '')
                url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"
                if not url.startswith("http"):
                    url = f"https://www.youtube.com/watch?v={url}"

                tracks.append(Track(
                    title=entry.get('title', 'Unknown Track'),
                    artist=entry.get('uploader') or entry.get('channel') or entry.get('artist') or 'Various',
                    video_id=video_id,
                    url=url,
                    duration_seconds=entry.get('duration') or 0
                ))
    except Exception as e:
        logger.error(f"Failed to extract playlist tracks: {e}")

    return tracks
