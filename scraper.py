import os
import json
import logging
from typing import List, Dict, Any, Optional

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

    @staticmethod
    def extract_playlist_id(raw_input: str) -> str:
        """Extracts the clean playlist ID from a raw ID or full YouTube / YouTube Music URL."""
        raw_input = raw_input.strip()
        if "list=" in raw_input:
            import urllib.parse
            parsed = urllib.parse.urlparse(raw_input)
            params = urllib.parse.parse_qs(parsed.query)
            if "list" in params and params["list"]:
                return params["list"][0]
        return raw_input

    def get_top_songs(self, limit: int = 7, playlist_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches candidate songs from:
        1. An unlisted/public playlist (if playlist_id provided) - 100% unauthenticated & safe
        2. User playback history (if authenticated)
        3. YouTube Music trending charts (fallback)
        """
        songs = []
        if not self.ytm:
            return songs

        # 1. Fetch from Unlisted / Public Playlist if provided (No Google account required)
        if playlist_id:
            clean_id = self.extract_playlist_id(playlist_id)
            if clean_id:
                try:
                    logging.info(f"Fetching candidate tracks from unlisted/public playlist (ID: {clean_id})...")
                    playlist_data = self.ytm.get_playlist(clean_id)
                    tracks = playlist_data.get("tracks", [])
                    # Reverse so recently added songs appear first
                    for item in reversed(tracks):
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
                        if len(songs) >= limit:
                            break
                    if songs:
                        logging.info(f"Loaded {len(songs)} tracks from playlist '{playlist_data.get('title', clean_id)}'")
                        return songs
                except Exception as e:
                    logging.warning(f"Failed to fetch playlist '{clean_id}': {e}. Falling back...")

        # 2. Try authenticated personal history if credentials present
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
