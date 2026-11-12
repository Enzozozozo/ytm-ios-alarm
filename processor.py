import os
import logging
from typing import Optional, Tuple
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def find_peak_energy_window(audio: AudioSegment, window_ms: int, step_ms: int = 500) -> Tuple[int, float]:
    total_len = len(audio)
    if total_len <= window_ms:
        return 0, audio.dBFS

    search_end = max(0, total_len - window_ms)
    search_start = min(min(5000, total_len // 6), search_end)

    max_db = -float("inf")
    best_start = search_start

    for start in range(search_start, search_end + 1, step_ms):
        chunk = audio[start:start + window_ms]
        db = chunk.dBFS
        if db > max_db:
            max_db = db
            best_start = start

    return best_start, max_db

def create_alarm_snippet(
    audio_file_path: str,
    output_path: str,
    snippet_duration_sec: int = 15,
    fade_in_ms: int = 1000,
    fade_out_ms: int = 1000
) -> Optional[str]:
    try:
        audio = AudioSegment.from_file(audio_file_path)
        window_ms = snippet_duration_sec * 1000
        start_ms, peak_db = find_peak_energy_window(audio, window_ms)
        end_ms = min(len(audio), start_ms + window_ms)

        logger.info(f"Peak window: {start_ms / 1000:.1f}s - {end_ms / 1000:.1f}s ({peak_db:.1f} dBFS)")
        snippet = audio[start_ms:end_ms]

        max_fade = len(snippet) // 2
        f_in = min(fade_in_ms, max_fade)
        f_out = min(fade_out_ms, max_fade)
        snippet = snippet.fade_in(f_in).fade_out(f_out)

        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)

        tmp_path = os.path.join(out_dir, f".tmp_{os.path.basename(output_path)}")
        snippet.export(tmp_path, format="ipod")
        os.replace(tmp_path, output_path)

        return output_path
    except Exception as e:
        logger.error(f"Error extracting audio snippet: {e}")
        return None
