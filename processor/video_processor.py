"""
Core video processing module for Quick Cut video editor.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.fx.all import fadein, fadeout

from processor.audio_analyzer import AudioAnalyzer
from processor.video_editor import VideoEditor

class VideoProcessor:
    """Core video processing engine that coordinates audio analysis and video editing."""
    
    def __init__(self, silence_threshold: float = -40.0, min_silence_duration: float = 2.0,
                 fade_duration: float = 0.1, progress_callback: Optional[Callable] = None):
        """
        Initialize the video processor.
        
        Args:
            silence_threshold: dB level below which audio is considered silence
            min_silence_duration: minimum duration of silence to remove (seconds)
            fade_duration: duration of fade in/out transitions (seconds)
            progress_callback: optional callback function for progress updates
        """
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.fade_duration = fade_duration
        self.progress_callback = progress_callback or self._default_progress_callback
        
        # Initialize components
        self.audio_analyzer = AudioAnalyzer(silence_threshold, min_silence_duration)
        self.video_editor = VideoEditor(fade_duration)
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the current processing run."""
        self._cancelled = True
        self.progress_callback(0, "Cancelling...")

    def _default_progress_callback(self, progress: float, message: str = "") -> None:
        """Default progress callback that prints to console."""
        print(f"Progress: {progress:.1f}% - {message}")

    def process_video(self, input_path: str, output_path: str, 
                     enable_fade_transitions: bool = True,
                     enable_audio_normalization: bool = True) -> bool:
        """
        Process a video file to remove silent sections.
        
        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            enable_fade_transitions: Whether to apply fade transitions
            enable_audio_normalization: Whether to normalize audio
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            self.progress_callback(0, "Loading video file...")
            
            # Validate input file
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Load video
            video_clip = VideoFileClip(input_path)
            original_duration = video_clip.duration
            
            if self._cancelled:
                video_clip.close()
                self.progress_callback(0, "Processing cancelled")
                return False

            self.progress_callback(10, "Extracting audio...")
            
            # Extract audio for analysis
            audio_segment = self.audio_analyzer.load_audio_from_video(input_path)
            if self._cancelled:
                video_clip.close()
                self.progress_callback(0, "Processing cancelled")
                return False
            if audio_segment is None:
                # Fallback gracefully when video has no audio track
                self.progress_callback(20, "No audio track detected; exporting original video")
                try:
                    self._export_clip(video_clip, output_path)
                finally:
                    video_clip.close()
                self.progress_callback(100, "Processing complete!")
                return True
            
            self.progress_callback(20, "Running ASR to detect speech and fillers...")
            
            # ASR is mandatory: derive speech segments from recognized word timestamps
            try:
                from processor.asr_filler_detector import ASRFillerDetector
                detector = ASRFillerDetector()
                if not detector.enabled:
                    self.progress_callback(20, "ASR model not available; install Vosk model (see README)")
                    video_clip.close()
                    raise RuntimeError("ASR model not available")

                # Map ASR progress into UI: speech 20-24%, fillers 24-28%
                speech_segments = detector.detect_speech_segments(
                    audio_segment,
                    progress_cb=self.progress_callback,
                    start_pct=20.0,
                    end_pct=24.0
                )
                filler_segments = detector.detect_fillers(
                    audio_segment,
                    progress_cb=self.progress_callback,
                    start_pct=24.0,
                    end_pct=28.0
                )
                if filler_segments:
                    self.progress_callback(28, f"Detected {len(filler_segments)} filler ranges via ASR")
                    speech_segments = self._subtract_intervals(speech_segments, filler_segments)
            except Exception as e:
                # Any ASR error should fail processing when ASR is mandatory
                video_clip.close()
                raise

            if not speech_segments:
                # No speech recognized by ASR -> fail with clear message
                video_clip.close()
                raise RuntimeError("No speech detected by ASR; nothing to cut")
            
            self.progress_callback(30, f"Found {len(speech_segments)} speech segments (ASR)")
            
            # Calculate expected output duration
            expected_duration = sum(end - start for start, end in speech_segments)
            
            self.progress_callback(40, "Creating video segments...")
            
            # Create video segments from speech portions
            video_segments = []
            for i, (start_time, end_time) in enumerate(speech_segments):
                segment_progress = 40 + (50 - 40) * (i + 1) / len(speech_segments)
                self.progress_callback(segment_progress, f"Processing segment {i + 1}/{len(speech_segments)}")
                
                # Extract video segment
                segment = video_clip.subclip(start_time, end_time)
                
                # Apply fade transitions if enabled
                if enable_fade_transitions:
                    segment = self.video_editor.apply_fade_transitions(segment)
                
                video_segments.append(segment)
                
                if self._cancelled:
                    for s in video_segments:
                        s.close()
                    video_clip.close()
                    self.progress_callback(0, "Processing cancelled")
                    return False
            
            self.progress_callback(50, "Concatenating video segments...")
            
            # Concatenate all segments using compose to handle any slight differences
            try:
                final_video = concatenate_videoclips(video_segments, method="compose")
            except Exception as e:
                # Fallback to original video if concatenation fails
                self.progress_callback(55, f"Concatenation failed; exporting original video: {e}")
                for s in video_segments:
                    s.close()
                try:
                    self._export_clip(video_clip, output_path)
                finally:
                    video_clip.close()
                self.progress_callback(100, "Processing complete!")
                return True
            
            if self._cancelled:
                final_video.close()
                for s in video_segments:
                    s.close()
                video_clip.close()
                self.progress_callback(0, "Processing cancelled")
                return False
            
            # Apply audio normalization if enabled
            if enable_audio_normalization:
                self.progress_callback(70, "Normalizing audio...")
                final_video = self.video_editor.normalize_audio(final_video)
            
            self.progress_callback(80, "Writing final video to disk...")
            
            # Export final video
            output_format = Path(output_path).suffix.lower()
            codec_settings = self._get_codec_settings(output_format)
            temp_ext = self._get_temp_audio_extension(codec_settings['audio_codec'])
            
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            try:
                export_logger = self._create_export_logger(80.0, 99.0, "Writing final video to disk...")
                final_video.write_videofile(
                    output_path,
                    codec=codec_settings['codec'],
                    audio_codec=codec_settings['audio_codec'],
                    temp_audiofile=tempfile.mktemp(suffix=temp_ext),
                    remove_temp=True,
                    verbose=False,
                    logger=export_logger,
                    fps=video_clip.fps,
                    audio=final_video.audio is not None
                )
            except Exception:
                # Attempt a codec/container-specific fallback
                self.progress_callback(85, "Export failed; retrying with safe codec settings...")
                fallback = self._get_safe_codec_settings(output_format)
                temp_ext = self._get_temp_audio_extension(fallback['audio_codec'])
                export_logger = self._create_export_logger(85.0, 99.0, "Writing final video (retry) to disk...")
                final_video.write_videofile(
                    output_path,
                    codec=fallback['codec'],
                    audio_codec=fallback['audio_codec'],
                    temp_audiofile=tempfile.mktemp(suffix=temp_ext),
                    remove_temp=True,
                    verbose=False,
                    logger=export_logger,
                    fps=video_clip.fps,
                    audio=final_video.audio is not None
                )
            
            # Clean up
            video_clip.close()
            final_video.close()
            for segment in video_segments:
                segment.close()
            
            self.progress_callback(100, "Processing complete!")
            
            return True
        except Exception as e:
            self.progress_callback(0, f"Error: {str(e)}")
            print(f"Video processing error: {e}")
            return False

    def _get_codec_settings(self, format_extension: str) -> dict:
        """Get codec settings for different output formats."""
        codec_map = {
            '.mp4': {'codec': 'libx264', 'audio_codec': 'aac'},
            '.avi': {'codec': 'mpeg4', 'audio_codec': 'libmp3lame'},
            '.mov': {'codec': 'libx264', 'audio_codec': 'aac'},
            '.mkv': {'codec': 'libx264', 'audio_codec': 'aac'},
            '.wmv': {'codec': 'wmv2', 'audio_codec': 'wmav2'},
            '.flv': {'codec': 'flv', 'audio_codec': 'libmp3lame'},
        }
        return codec_map.get(format_extension, {'codec': 'libx264', 'audio_codec': 'aac'})

    def _get_safe_codec_settings(self, format_extension: str) -> dict:
        """Fallback codec settings intended to maximize compatibility."""
        return self._get_codec_settings(format_extension)

    def _get_temp_audio_extension(self, audio_codec: str) -> str:
        """Return a suitable temp audio file extension for the given codec."""
        mapping = {
            'aac': '.m4a',
            'libmp3lame': '.mp3',
            'mp3': '.mp3',
            'wav': '.wav',
            'flac': '.flac',
            'wmav2': '.wav',  # use wav container for wma codec
        }
        return mapping.get(audio_codec, '.m4a')

    def _export_clip(self, clip, output_path: str) -> None:
        """Export a single clip using container-appropriate codec settings."""
        output_format = Path(output_path).suffix.lower()
        codec_settings = self._get_codec_settings(output_format)
        temp_ext = self._get_temp_audio_extension(codec_settings['audio_codec'])
        os.makedirs(Path(output_path).parent, exist_ok=True)
        export_logger = self._create_export_logger(80.0, 99.0, "Writing final video to disk...")
        clip.write_videofile(
            output_path,
            codec=codec_settings['codec'],
            audio_codec=codec_settings['audio_codec'],
            temp_audiofile=tempfile.mktemp(suffix=temp_ext),
            remove_temp=True,
            verbose=False,
            logger=export_logger,
            fps=clip.fps if hasattr(clip, 'fps') and clip.fps else 24,
            audio=clip.audio is not None
        )

    def analyze_video(self, video_path: str) -> dict:
        """
        Analyze a video file and return information about silence and speech segments.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Load video to get duration
            video_clip = VideoFileClip(video_path)
            original_duration = video_clip.duration
            video_clip.close()
            
            # Extract and analyze audio
            audio_segment = self.audio_analyzer.load_audio_from_video(video_path)
            if audio_segment is None:
                return {'error': 'Could not extract audio from video'}
            
            # ASR is mandatory: use word timestamps for speech segments
            from processor.asr_filler_detector import ASRFillerDetector
            detector = ASRFillerDetector()
            if not detector.enabled:
                return {'error': 'ASR model not available. Please install a Vosk model and set VOSK_MODEL.'}
            
            speech_segments = detector.detect_speech_segments(audio_segment)
            filler_segments = detector.detect_fillers(audio_segment)
            if filler_segments:
                speech_segments = self._subtract_intervals(speech_segments, filler_segments)
            
            # Calculate statistics
            total_speech_time = sum(end - start for start, end in speech_segments)
            silence_time = original_duration - total_speech_time
            silence_percentage = (silence_time / original_duration) * 100 if original_duration > 0 else 0
            
            return {
                'original_duration': original_duration,
                'speech_segments': speech_segments,
                'total_speech_time': total_speech_time,
                'silence_time': silence_time,
                'silence_percentage': silence_percentage,
                'expected_output_duration': total_speech_time,
                'time_saved': silence_time
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def set_silence_threshold(self, threshold: float) -> None:
        """Set the silence threshold."""
        self.silence_threshold = threshold
        self.audio_analyzer.set_silence_threshold(threshold)
    
    
    def set_min_silence_duration(self, duration: float) -> None:
        """Set the minimum silence duration."""
        self.min_silence_duration = duration
        self.audio_analyzer.set_min_silence_duration(duration)
    
    def set_fade_duration(self, duration: float) -> None:
        """Set the fade duration."""
        self.fade_duration = duration
        self.video_editor.set_fade_duration(duration)

    def _subtract_intervals(self, base: List[Tuple[float, float]], cuts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Subtract cut intervals from base intervals and return the remaining parts."""
        if not base:
            return []
        if not cuts:
            return base
        base = sorted(base, key=lambda x: x[0])
        cuts = sorted(cuts, key=lambda x: x[0])
        result: List[Tuple[float, float]] = []
        i = 0
        for s, e in base:
            cs, ce = s, e
            while i < len(cuts) and cuts[i][1] <= cs:
                i += 1
            j = i
            cur = cs
            while j < len(cuts) and cuts[j][0] < ce:
                cut_s, cut_e = cuts[j]
                if cut_s > cur:
                    result.append((cur, min(cut_s, ce)))
                cur = max(cur, cut_e)
                if cur >= ce:
                    break
                j += 1
            if cur < ce:
                result.append((cur, ce))
        return result

    def _merge_intervals(self, intervals: List[Tuple[float, float]], min_gap: float = 0.0) -> List[Tuple[float, float]]:
        """Merge overlapping or nearly-adjacent intervals."""
        if not intervals:
            return []
        intervals = sorted(intervals, key=lambda x: x[0])
        merged: List[Tuple[float, float]] = []
        cs, ce = intervals[0]
        for s, e in intervals[1:]:
            if s <= ce + min_gap:
                ce = max(ce, e)
            else:
                merged.append((cs, ce))
                cs, ce = s, e
        merged.append((cs, ce))
        return merged

    def _create_export_logger(self, start_pct: float, end_pct: float, prefix: str):
        """Create a proglog-based logger that maps MoviePy export progress to UI.
        Returns None if proglog is unavailable.
        """
        try:
            from proglog import ProgressBarLogger
        except Exception:
            return None
        
        class _CallbackLogger(ProgressBarLogger):
            def __init__(self, cb, s, e, p):
                super().__init__()
                self._cb = cb
                self._start = float(s)
                self._end = float(e)
                self._prefix = p
            
            def bars_callback(self, bar, attr, value, old_value=None):
                # Track the main time bar ('t') index updates
                try:
                    if bar == 't' and attr == 'index':
                        total = self.bars.get('t', {}).get('total', 0) or 0
                        index = value or 0
                        if total:
                            frac = max(0.0, min(1.0, float(index) / float(total)))
                            pct = self._start + (self._end - self._start) * frac
                            # Round progress to one decimal for smooth movement
                            self._cb(pct, f"{self._prefix} ({int(index)}/{int(total)})")
                except Exception:
                    # Silently ignore logging issues to avoid breaking export
                    pass
        
        return _CallbackLogger(self.progress_callback, start_pct, end_pct, prefix)