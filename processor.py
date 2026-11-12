import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AudioProcessor:
    def __init__(self, snippet_duration_sec: int = 30, fade_in_ms: int = 1000, fade_out_ms: int = 1500):
        self.snippet_duration_sec = snippet_duration_sec
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms

    def find_peak_energy_window(self, audio_segment, window_ms: int) -> int:
        """
        Calculates Root-Mean-Square (RMS) loudness across sliding windows
        to identify the loudest/most energetic part (typically the chorus/drop).
        """
        step_ms = 1000  # 1-second steps
        total_len = len(audio_segment)
        if total_len <= window_ms:
            return 0

        max_rms = -1
        best_start = 0

        # Don't pick the first 15 seconds if the track is reasonably long (avoids quiet intros)
        search_start = min(15000, total_len // 4)
        search_end = total_len - window_ms

        for start in range(search_start, search_end, step_ms):
            chunk = audio_segment[start:start + window_ms]
            rms = chunk.rms
            if rms > max_rms:
                max_rms = rms
                best_start = start

        return best_start

    def extract_snippet(self, audio_file_path: str, output_path: str) -> Optional[str]:
        """
        Extracts the peak 30s audio snippet, applies fading, and exports
        as an iOS-compatible AAC/m4a file.
        """
        try:
            from pydub import AudioSegment
            logging.info(f"Loading {audio_file_path} for snippet extraction...")
            audio = AudioSegment.from_file(audio_file_path)

            window_ms = self.snippet_duration_sec * 1000
            start_ms = self.find_peak_energy_window(audio, window_ms)
            end_ms = min(len(audio), start_ms + window_ms)

            logging.info(f"Peak energy window detected at {start_ms // 1000}s - {end_ms // 1000}s")
            snippet = audio[start_ms:end_ms]

            # Apply smooth crossfades
            snippet = snippet.fade_in(self.fade_in_ms).fade_out(self.fade_out_ms)

            # Ensure output folder exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # Export as m4a / AAC for native iOS playback
            snippet.export(output_path, format="ipod")
            logging.info(f"Alarm snippet saved to: {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error processing audio snippet: {e}")
            return None
