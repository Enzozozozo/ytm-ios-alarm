from dataclasses import dataclass

@dataclass(frozen=True)
class Track:
    title: str
    artist: str
    video_id: str
    url: str
    duration_seconds: int = 0
