"""
Audio analysis module for silence detection in video files.
"""

import numpy as np
from typing import List, Tuple, Optional
from pydub import AudioSegment
from pydub.utils import get_array_type
import wave
import tempfile
import os

class AudioAnalyzer:
    """Analyzes audio to detect silence and speech segments."""
    
    def __init__(self, silence_threshold: float = -40.0, min_silence_duration: float = 0.5):
        """
        Initialize the audio analyzer.
        
        Args:
            silence_threshold: dB level below which audio is considered silence
            min_silence_duration: minimum duration of silence to be removed (seconds)
        """
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.frame_duration = 0.1  # 100ms frames for analysis

    def load_audio_from_video(self, video_path: str) -> Optional[AudioSegment]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            AudioSegment object or None if extraction fails
        """
        try:
            # Create a temporary audio file
            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_audio.close()
            
            # Use moviepy to extract audio (will be imported in video_processor)
            from moviepy.editor import VideoFileClip
            
            video = VideoFileClip(video_path)
            audio = video.audio
            
            if audio is None:
                return None
            
            # Write audio to temporary file
            audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
            video.close()
            
            # Load with pydub
            audio_segment = AudioSegment.from_wav(temp_audio.name)
            
            # Clean up temp file
            os.unlink(temp_audio.name)
            
            return audio_segment
            
        except Exception as e:
            print(f"Error extracting audio from video: {e}")
            return None

    def calculate_rms_energy(self, audio_segment: AudioSegment, frame_duration: float = 0.1) -> List[float]:
        """
        Calculate RMS energy for audio frames.
        
        Args:
            audio_segment: AudioSegment to analyze
            frame_duration: Duration of each frame in seconds
            
        Returns:
            List of RMS energy values
        """
        frame_length = int(frame_duration * 1000)  # Convert to milliseconds
        rms_values = []
        
        for i in range(0, len(audio_segment), frame_length):
            frame = audio_segment[i:i + frame_length]
            samples = np.array(frame.get_array_of_samples())
            
            if len(samples) > 0:
                rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
                rms_values.append(rms)
            else:
                rms_values.append(0.0)
        
        return rms_values

    def rms_to_db(self, rms_value: float, reference_rms: float = 1.0) -> float:
        """
        Convert RMS value to decibels.
        
        Args:
            rms_value: RMS value to convert
            reference_rms: Reference RMS value
            
        Returns:
            dB value
        """
        if rms_value <= 0:
            return -60.0  # Minimum dB value
        
        return 20 * np.log10(rms_value / reference_rms)

    def _compute_db_values(self, audio_segment: AudioSegment) -> List[float]:
        """Compute per-frame dB levels for the given audio segment."""
        rms_values = self.calculate_rms_energy(audio_segment, self.frame_duration)
        db_values = [self.rms_to_db(rms) for rms in rms_values]
        return db_values

    def _adaptive_threshold(self, db_values: List[float]) -> float:
        """
        Compute an adaptive threshold based on the noise floor.
        
        Uses the 20th percentile of frame dB levels as the noise floor and
        adds a margin to distinguish speech from background noise.
        """
        if not db_values:
            return self.silence_threshold
        
        noise_floor = float(np.percentile(db_values, 20))
        margin_db = 6.0  # how much above noise floor we consider speech
        dynamic_threshold = noise_floor + margin_db
        # Ensure we don't go below the configured static threshold
        effective_threshold = max(self.silence_threshold, dynamic_threshold)
        # Clamp to a reasonable upper bound to avoid over-cutting
        effective_threshold = min(effective_threshold, -20.0)
        return effective_threshold

    def _compute_speech_band_ratio(self, audio_segment: AudioSegment) -> List[float]:
        """
        Estimate per-frame ratio of energy in the speech band (300–3400 Hz).
        Frames dominated by low-frequency noise will have low ratios.
        """
        frame_length = int(self.frame_duration * 1000)
        ratios: List[float] = []
        sr = audio_segment.frame_rate
        for i in range(0, len(audio_segment), frame_length):
            frame = audio_segment[i:i + frame_length]
            samples = np.array(frame.get_array_of_samples())
            if len(samples) == 0:
                ratios.append(0.0)
                continue
            # Handle multi-channel by averaging to mono
            if frame.channels > 1:
                samples = samples.reshape((-1, frame.channels)).mean(axis=1)
            samples = samples.astype(np.float32)
            # Apply a simple Hann window to reduce spectral leakage
            n = len(samples)
            if n == 0:
                ratios.append(0.0)
                continue
            window = np.hanning(n)
            x = samples * window
            # Real FFT
            spec = np.fft.rfft(x)
            mag2 = np.abs(spec) ** 2
            freqs = np.fft.rfftfreq(n, d=1.0 / sr)
            total_energy = float(np.sum(mag2))
            if total_energy <= 0:
                ratios.append(0.0)
                continue
            band_mask = (freqs >= 300.0) & (freqs <= 3400.0)
            band_energy = float(np.sum(mag2[band_mask]))
            ratios.append(band_energy / total_energy)
        return ratios

    def detect_silence_segments(self, audio_segment: AudioSegment) -> List[Tuple[float, float]]:
        """
        Detect silence segments in audio.
        
        Args:
            audio_segment: AudioSegment to analyze
            
        Returns:
            List of (start_time, end_time) tuples for silence segments
        """
        # Compute dB values per frame
        db_values = self._compute_db_values(audio_segment)
        # Compute speech band ratios per frame
        band_ratios = self._compute_speech_band_ratio(audio_segment)
        
        # Use an adaptive threshold to better reject background noise
        effective_threshold = self._adaptive_threshold(db_values)
        
        silence_segments = []
        current_segment_start = None
        
        for i, db_level in enumerate(db_values):
            start_time = i * self.frame_duration
            end_time = (i + 1) * self.frame_duration
            ratio = band_ratios[i] if i < len(band_ratios) else 0.0
            
            # Consider a frame silent if it's below the adaptive threshold
            # or slightly above but clearly dominated by non-speech frequencies
            if (db_level < effective_threshold) or (db_level < effective_threshold + 3.0 and ratio < 0.35):
                if current_segment_start is None:
                    current_segment_start = start_time
            else:
                if current_segment_start is not None:
                    segment_duration = end_time - current_segment_start
                    if segment_duration >= self.min_silence_duration:
                        silence_segments.append((current_segment_start, end_time))
                    current_segment_start = None
        
        # Handle silence that extends to the end
        if current_segment_start is not None:
            segment_duration = len(db_values) * self.frame_duration - current_segment_start
            if segment_duration >= self.min_silence_duration:
                silence_segments.append((current_segment_start, len(db_values) * self.frame_duration))
        
        return silence_segments
    
    def find_speech_segments(self, audio_segment: AudioSegment) -> List[Tuple[float, float]]:
        """
        Find speech segments using energy and speech-band criteria.
        
        Args:
            audio_segment: AudioSegment to analyze
            
        Returns:
            List of (start_time, end_time) tuples for speech segments
        """
        # Compute features
        db_values = self._compute_db_values(audio_segment)
        band_ratios = self._compute_speech_band_ratio(audio_segment)
        threshold = self._adaptive_threshold(db_values)
        
        speech_segments: List[Tuple[float, float]] = []
        current_start: Optional[float] = None
        
        for i, db_level in enumerate(db_values):
            start_time = i * self.frame_duration
            end_time = (i + 1) * self.frame_duration
            ratio = band_ratios[i] if i < len(band_ratios) else 0.0
            # Speech if energy is near/above threshold and spectral content indicates speech
            is_speech = (db_level >= threshold - 2.0) and (ratio >= 0.35)
            if is_speech:
                if current_start is None:
                    current_start = start_time
            else:
                if current_start is not None:
                    # End of speech segment
                    duration = end_time - current_start
                    speech_segments.append((current_start, end_time))
                    current_start = None
        
        if current_start is not None:
            # handle tail
            total_time = len(db_values) * self.frame_duration
            duration = total_time - current_start
            speech_segments.append((current_start, total_time))
        
        # If nothing detected, fallback to non-silence method
        if not speech_segments:
            return self._fallback_speech_segments(audio_segment)
        
        return speech_segments

    def _fallback_speech_segments(self, audio_segment: AudioSegment) -> List[Tuple[float, float]]:
        """Fallback: treat non-silent portions as speech (original behavior)."""
        silence_segments = self.detect_silence_segments(audio_segment)
        total_duration = len(audio_segment) / 1000.0
        if not silence_segments:
            return [(0.0, total_duration)]
        speech_segments = []
        current_start = 0.0
        for silence_start, silence_end in silence_segments:
            if current_start < silence_start:
                speech_segments.append((current_start, silence_start))
            current_start = silence_end
        if current_start < total_duration:
            speech_segments.append((current_start, total_duration))
        return speech_segments
    
    def get_audio_info(self, audio_segment: AudioSegment) -> dict:
        """
        Get basic audio information.
        
        Args:
            audio_segment: AudioSegment to analyze
            
        Returns:
            Dictionary with audio information
        """
        return {
            'duration': len(audio_segment) / 1000.0,  # seconds
            'channels': audio_segment.channels,
            'frame_rate': audio_segment.frame_rate,
            'sample_width': audio_segment.sample_width,
            'max_amplitude': audio_segment.max,
            'rms': audio_segment.rms
        }
    
    def set_silence_threshold(self, threshold: float) -> None:
        """Set the silence threshold in dB."""
        self.silence_threshold = threshold
    
    def set_min_silence_duration(self, duration: float) -> None:
        """Set the minimum silence duration in seconds."""
        self.min_silence_duration = duration