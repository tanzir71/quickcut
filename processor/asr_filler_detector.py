"""
ASR-based filler word detector using Vosk.
Detects short interjections like "um", "uh", "umm", etc., with word-level timestamps
and returns time ranges to be removed from the final edit.
"""
from typing import List, Tuple, Optional, Callable
import os
import json
import urllib.request
import zipfile
from pathlib import Path

try:
    import vosk  # type: ignore
except Exception:
    vosk = None  # Optional dependency; detector will gracefully disable

from pydub import AudioSegment


class ASRFillerDetector:
    """Detect filler words using offline ASR (Vosk)."""

    def __init__(self, model_dir: Optional[str] = None, languages: Optional[List[str]] = None):
        """
        Args:
            model_dir: Path to a Vosk model directory (word-level timestamps supported).
            languages: Optional language hints (unused for Vosk model path selection).
        """
        self.enabled = vosk is not None
        self.model = None

        if not self.enabled:
            return

        # Resolve model directory
        model_dir = model_dir or os.environ.get("VOSK_MODEL")
        if not model_dir:
            # Try common local paths
            candidates = [
                os.path.join("models", "vosk-model-small-en-us-0.15"),
                os.path.join("models", "vosk-model-en-us-0.22"),
            ]
            for c in candidates:
                if os.path.isdir(c):
                    model_dir = c
                    break

        # Auto-download English model if not found
        if not model_dir:
            try:
                target_root = Path(__file__).resolve().parent.parent / "models"
                model_dir = self._auto_download_english_model(str(target_root))
            except Exception:
                model_dir = None

        if model_dir and os.path.isdir(model_dir):
            try:
                self.model = vosk.Model(model_dir)
            except Exception:
                self.model = None

        self.enabled = self.model is not None

        # Filler lexicon
        self.filler_set = {
            "um", "uh", "umm", "uhh", "erm", "er", "ah", "eh", "mm", "hmm"
        }
        # Merge adjacent fillers if gap < threshold (seconds)
        self.merge_gap_seconds = 0.25
        # Merge adjacent recognized words into speech segments when gap < threshold
        self.speech_merge_gap_seconds = 0.5

    def detect_fillers(self, audio_segment: AudioSegment, progress_cb: Optional[Callable[[float, str], None]] = None, start_pct: float = 24.0, end_pct: float = 28.0) -> List[Tuple[float, float]]:
        """Return filler word time ranges as (start, end) in seconds.

        If ASR dependency or model is unavailable, returns an empty list.
        """
        if not self.enabled or self.model is None:
            return []

        # Prepare mono 16 kHz, 16-bit PCM
        seg = audio_segment.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        raw = seg.raw_data
        rate = 16000

        rec = vosk.KaldiRecognizer(self.model, rate)
        rec.SetWords(True)

        fillers: List[Tuple[float, float]] = []

        # Stream bytes to recognizer in ~0.25s chunks (8000 bytes at 16kHz*2 bytes)
        chunk_size = int(0.25 * rate) * 2
        total_chunks = max(1, (len(raw) + chunk_size - 1) // chunk_size)
        for idx, i in enumerate(range(0, len(raw), chunk_size), start=1):
            chunk = raw[i:i + chunk_size]
            if rec.AcceptWaveform(chunk):
                try:
                    res = json.loads(rec.Result())
                    self._collect_fillers_from_result(res, fillers)
                except Exception:
                    pass
            else:
                # partial result not used for timings
                _ = rec.PartialResult()
            # progress update
            if progress_cb:
                frac = idx / float(total_chunks)
                pct = start_pct + (end_pct - start_pct) * frac
                progress_cb(pct, f"Running ASR (fillers)... ({idx}/{total_chunks})")

        # Final flush
        try:
            final_res = json.loads(rec.FinalResult())
            self._collect_fillers_from_result(final_res, fillers)
        except Exception:
            pass

        # Merge adjacent filler ranges with small gaps
        fillers = self._merge_adjacent(fillers, self.merge_gap_seconds)
        if progress_cb:
            progress_cb(end_pct, f"Running ASR (fillers)... ({total_chunks}/{total_chunks})")
        return fillers

    def _collect_fillers_from_result(self, res: dict, out: List[Tuple[float, float]]) -> None:
        words = res.get("result", [])
        for w in words:
            word = str(w.get("word", "")).lower()
            if word in self.filler_set:
                start = float(w.get("start", 0.0))
                end = float(w.get("end", start))
                if end > start:
                    out.append((start, end))

    def detect_speech_segments(self, audio_segment: AudioSegment, progress_cb: Optional[Callable[[float, str], None]] = None, start_pct: float = 20.0, end_pct: float = 24.0) -> List[Tuple[float, float]]:
        """Return speech segments using recognized word timestamps.

        Groups contiguous recognized words, merging gaps smaller than
        `self.speech_merge_gap_seconds`. If ASR is unavailable, returns [].
        """
        if not self.enabled or self.model is None:
            return []

        # Prepare mono 16 kHz, 16-bit PCM
        seg = audio_segment.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        raw = seg.raw_data
        rate = 16000

        rec = vosk.KaldiRecognizer(self.model, rate)
        rec.SetWords(True)

        word_intervals: List[Tuple[float, float]] = []

        chunk_size = int(0.25 * rate) * 2
        total_chunks = max(1, (len(raw) + chunk_size - 1) // chunk_size)
        for idx, i in enumerate(range(0, len(raw), chunk_size), start=1):
            chunk = raw[i:i + chunk_size]
            if rec.AcceptWaveform(chunk):
                try:
                    res = json.loads(rec.Result())
                    self._collect_words_from_result(res, word_intervals)
                except Exception:
                    pass
            else:
                _ = rec.PartialResult()
            if progress_cb:
                frac = idx / float(total_chunks)
                pct = start_pct + (end_pct - start_pct) * frac
                progress_cb(pct, f"Running ASR (speech)... ({idx}/{total_chunks})")

        try:
            final_res = json.loads(rec.FinalResult())
            self._collect_words_from_result(final_res, word_intervals)
        except Exception:
            pass

        # Merge adjacent words into continuous speech ranges
        if progress_cb:
            progress_cb(end_pct, f"Running ASR (speech)... ({total_chunks}/{total_chunks})")
        return self._merge_adjacent(word_intervals, self.speech_merge_gap_seconds)

    def _collect_words_from_result(self, res: dict, out: List[Tuple[float, float]]) -> None:
        """Collect intervals for all recognized words in an ASR result."""
        words = res.get("result", [])
        for w in words:
            start = float(w.get("start", 0.0))
            end = float(w.get("end", start))
            if end > start:
                out.append((start, end))

    @staticmethod
    def _merge_adjacent(ranges: List[Tuple[float, float]], max_gap: float) -> List[Tuple[float, float]]:
        if not ranges:
            return []
        ranges = sorted(ranges, key=lambda x: x[0])
        merged = []
        cs, ce = ranges[0]
        for s, e in ranges[1:]:
            if s <= ce + max_gap:
                ce = max(ce, e)
            else:
                merged.append((cs, ce))
                cs, ce = s, e
        merged.append((cs, ce))
        return merged


    def _auto_download_english_model(self, target_dir: str) -> Optional[str]:
        """Download and extract the default English Vosk model if missing.

        Returns the extracted model directory path, or None on failure.
        """
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception:
            pass
        zip_name = "vosk-model-small-en-us-0.15.zip"
        zip_path = os.path.join(target_dir, zip_name)
        model_folder = os.path.join(target_dir, "vosk-model-small-en-us-0.15")
        if os.path.isdir(model_folder):
            return model_folder

        urls = [
            "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "https://github.com/alphacep/vosk-api/releases/download/v0.3.43/vosk-model-small-en-us-0.15.zip",
        ]
        for url in urls:
            try:
                urllib.request.urlretrieve(url, zip_path)
                # sanity check size
                if os.path.getsize(zip_path) < 1_000_000:
                    continue
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(target_dir)
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
                if os.path.isdir(model_folder):
                    return model_folder
            except Exception:
                # Try next URL
                continue
        # Cleanup on failure
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass
        return None