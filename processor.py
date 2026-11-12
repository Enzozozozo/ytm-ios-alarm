import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AudioProcessor:
    def __init__(self, snippet_duration_sec: int = 15, fade_in_ms: int = 1000, fade_out_ms: int = 1000):
        self.snippet_duration_sec = snippet_duration_sec
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms

    def find_peak_energy_window(self, audio_segment, window_ms: int) -> tuple[int, float]:
        """
        Calculates Root-Mean-Square (RMS) loudness / mean dBFS across sliding windows
        in 500ms steps to identify the 15-second section with the highest mean dB.
        """
        step_ms = 500  # Fine-grained 0.5-second steps for high precision
        total_len = len(audio_segment)
        if total_len <= window_ms:
            return 0, audio_segment.dBFS

        max_db = -float("inf")
        best_start = 0

        # Avoid the first 5 seconds to bypass silent lead-in / intro clicks
        search_start = min(5000, total_len // 6)
        search_end = total_len - window_ms

        for start in range(search_start, search_end, step_ms):
            chunk = audio_segment[start:start + window_ms]
            db = chunk.dBFS
            if db > max_db:
                max_db = db
                best_start = start

        return best_start, max_db

    def extract_snippet(self, audio_file_path: str, output_path: str) -> Optional[str]:
        """
        Extracts the peak 15s audio snippet with highest mean dB, applies smooth fading,
        and exports as an iOS-compatible AAC/m4a file.
        """
        try:
            from pydub import AudioSegment
            logging.info(f"Loading {audio_file_path} for 15s peak dB snippet extraction...")
            audio = AudioSegment.from_file(audio_file_path)

            window_ms = self.snippet_duration_sec * 1000
            start_ms, peak_db = self.find_peak_energy_window(audio, window_ms)
            end_ms = min(len(audio), start_ms + window_ms)

            logging.info(f"15s peak loudness window: {start_ms / 1000:.1f}s - {end_ms / 1000:.1f}s (Mean loudness: {peak_db:.1f} dBFS)")
            snippet = audio[start_ms:end_ms]

            # Apply smooth crossfades
            snippet = snippet.fade_in(self.fade_in_ms).fade_out(self.fade_out_ms)

            # Ensure output folder exists
            out_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(out_dir, exist_ok=True)

            # Export atomically via temporary file to prevent corrupted partial artifacts
            tmp_path = os.path.join(out_dir, f".tmp_{os.path.basename(output_path)}")
            snippet.export(tmp_path, format="ipod")
            os.replace(tmp_path, output_path)

            logging.info(f"Alarm snippet saved to: {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error processing audio snippet: {e}")
            return None
