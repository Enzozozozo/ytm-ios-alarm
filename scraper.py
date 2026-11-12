import os
import json
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class YTMScraper:
    def __init__(self, auth_file: str = "oauth.json"):
        self.auth_file = auth_file
        self.ytm = None
        self._is_authenticated = False
        self._init_client()

    def _init_client(self):
        try:
            from ytmusicapi import YTMusic
            oauth_env = os.environ.get("YTM_OAUTH_JSON")
            if oauth_env:
                try:
                    auth_data = json.loads(oauth_env)
                    self.ytm = YTMusic(auth_data)
                    self._is_authenticated = True
                    logging.info("Authenticated via YTM_OAUTH_JSON environment variable")
                except json.JSONDecodeError:
                    self.ytm = YTMusic(oauth_env)
                    self._is_authenticated = True
                    logging.info("Authenticated via YTM_OAUTH_JSON filepath")
            elif os.path.exists(self.auth_file):
                self.ytm = YTMusic(self.auth_file)
                self._is_authenticated = True
                logging.info(f"Authenticated with {self.auth_file}")
            else:
                self._is_authenticated = False
                logging.warning(f"Auth file '{self.auth_file}' not found. Using unauthenticated public mode.")
                self.ytm = YTMusic()
        except ImportError:
            logging.error("ytmusicapi is not installed. Run 'pip install ytmusicapi'")
            self.ytm = None
            self._is_authenticated = False

    def get_top_songs(self, limit: int = 7) -> List[Dict[str, Any]]:
        """
        Fetches top listened tracks from user's history/recap.
        Falls back to trending/popular if auth is unavailable or expired.
        """
        songs = []
        if not self.ytm:
            return songs

        # 1. Try authenticated personal history if credentials present
        if self._is_authenticated:
            try:
                logging.info("Fetching user history / top tracks...")
                history = self.ytm.get_history()
                seen = set()
                for item in history:
                    video_id = item.get("videoId")
                    if video_id and video_id not in seen:
                        seen.add(video_id)
                        artists = ", ".join([a.get("name", "") for a in item.get("artists", [])])
                        songs.append({
                            "title": item.get("title", "Unknown Track"),
                            "artist": artists,
                            "video_id": video_id,
                            "url": f"https://music.youtube.com/watch?v={video_id}",
                            "duration_seconds": item.get("duration_seconds", 0)
                        })
                    if len(songs) >= limit:
                        break
            except Exception as e:
                logging.warning(f"Failed to fetch user history (session may be expired or challenged): {e}")
                logging.info("Degrading gracefully to public trending charts...")
                songs = []

        # 2. Fall back to trending tracks if history returned nothing
        if not songs:
            try:
                logging.info("Fetching top trending tracks from charts...")
                charts = self.ytm.get_charts(country="US")
                top_tracks = charts.get("videos", {}).get("items", []) or charts.get("tracks", {}).get("items", [])
                for item in top_tracks[:limit]:
                    video_id = item.get("videoId")
                    if video_id:
                        artists = ", ".join([a.get("name", "") for a in item.get("artists", [])])
                        songs.append({
                            "title": item.get("title", "Unknown Track"),
                            "artist": artists,
                            "video_id": video_id,
                            "url": f"https://music.youtube.com/watch?v={video_id}",
                            "duration_seconds": 0
                        })
            except Exception as e:
                logging.error(f"Error fetching trending charts from YouTube Music: {e}")

        return songs
