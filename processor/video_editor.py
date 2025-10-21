"""
Video editing utilities for segment manipulation and effects.
"""

from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.fx.all import fadein, fadeout
from moviepy.audio.fx.all import volumex, audio_fadein, audio_fadeout
import numpy as np

class VideoEditor:
    """Handles video segment manipulation and effects."""
    
    def __init__(self, fade_duration: float = 0.1):
        """
        Initialize the video editor.
        
        Args:
            fade_duration: Duration of fade in/out effects in seconds
        """
        self.fade_duration = fade_duration
    
    def apply_fade_transitions(self, video_clip) -> VideoFileClip:
        """
        Apply fade in and fade out transitions to a video clip.
        
        Args:
            video_clip: MoviePy VideoFileClip object
            
        Returns:
            VideoFileClip with fade transitions applied
        """
        # Apply audio fade in/out only to avoid black frames between cuts
        if self.fade_duration > 0 and video_clip.audio is not None:
            video_clip = video_clip.fx(audio_fadein, self.fade_duration)
            video_clip = video_clip.fx(audio_fadeout, self.fade_duration)
        
        return video_clip
    
    def normalize_audio(self, video_clip) -> VideoFileClip:
        """
        Normalize audio levels in a video clip.
        
        Args:
            video_clip: MoviePy VideoFileClip object
            
        Returns:
            VideoFileClip with normalized audio
        """
        if video_clip.audio is None:
            return video_clip
        
        try:
            # Calculate the maximum volume level
            audio_array = video_clip.audio.to_soundarray()
            max_volume = np.max(np.abs(audio_array))
            
            if max_volume > 0:
                # Calculate normalization factor (target -3dB from max)
                target_level = 0.7  # -3dB
                normalization_factor = target_level / max_volume
                
                # Apply volume adjustment
                video_clip = video_clip.fx(volumex, normalization_factor)
        except MemoryError:
            # If audio is too large to load into memory, skip normalization
            print("Warning: Skipping audio normalization due to memory constraints")
        except Exception as e:
            # Any other issue: keep original audio to avoid failing the pipeline
            print(f"Warning: Audio normalization failed: {e}")
        
        return video_clip
    
    def concatenate_segments(self, video_segments: list, apply_transitions: bool = True) -> VideoFileClip:
        """
        Concatenate multiple video segments into a single clip.
        
        Args:
            video_segments: List of VideoFileClip objects
            apply_transitions: Whether to apply fade transitions between segments
            
        Returns:
            Concatenated VideoFileClip
        """
        if not video_segments:
            raise ValueError("No video segments provided")
        
        if len(video_segments) == 1:
            return video_segments[0]
        
        # Apply transitions if requested
        if apply_transitions:
            processed_segments = []
            for i, segment in enumerate(video_segments):
                if i == 0:
                    # First segment: fade out only
                    if self.fade_duration > 0:
                        segment = fadeout(segment, self.fade_duration)
                elif i == len(video_segments) - 1:
                    # Last segment: fade in only
                    if self.fade_duration > 0:
                        segment = fadein(segment, self.fade_duration)
                else:
                    # Middle segments: fade in and out
                    if self.fade_duration > 0:
                        segment = fadein(segment, self.fade_duration)
                        segment = fadeout(segment, self.fade_duration)
                
                processed_segments.append(segment)
            
            return concatenate_videoclips(processed_segments)
        else:
            return concatenate_videoclips(video_segments)
    
    def extract_segment(self, video_clip, start_time: float, end_time: float) -> VideoFileClip:
        """
        Extract a segment from a video clip.
        
        Args:
            video_clip: MoviePy VideoFileClip object
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Extracted VideoFileClip segment
        """
        return video_clip.subclip(start_time, end_time)
    
    def change_speed(self, video_clip, speed_factor: float) -> VideoFileClip:
        """
        Change the playback speed of a video clip.
        
        Args:
            video_clip: MoviePy VideoFileClip object
            speed_factor: Speed multiplier (1.0 = normal speed)
            
        Returns:
            VideoFileClip with adjusted speed
        """
        return video_clip.fx(lambda clip: clip.speedx(speed_factor))
    
    def add_text_overlay(self, video_clip, text: str, position: str = 'bottom', 
                         duration: float = None, fontsize: int = 24) -> VideoFileClip:
        """
        Add text overlay to a video clip.
        
        Args:
            video_clip: MoviePy VideoFileClip object
            text: Text to overlay
            position: Position of text ('top', 'center', 'bottom')
            duration: Duration to show text (None = entire clip)
            fontsize: Font size in pixels
            
        Returns:
            VideoFileClip with text overlay
        """
        from moviepy.editor import TextClip, CompositeVideoClip
        
        # Create text clip
        text_clip = TextClip(text, fontsize=fontsize, color='white', 
                           font='Arial-Bold', stroke_color='black', stroke_width=2)
        
        # Position the text
        if position == 'top':
            text_clip = text_clip.set_position(('center', 'top'))
        elif position == 'center':
            text_clip = text_clip.set_position('center')
        else:  # bottom
            text_clip = text_clip.set_position(('center', 'bottom'))
        
        # Set duration
        if duration is None:
            text_clip = text_clip.set_duration(video_clip.duration)
        else:
            text_clip = text_clip.set_duration(duration)
        
        # Composite the text over the video
        return CompositeVideoClip([video_clip, text_clip])
    
    def resize_video(self, video_clip, width: int = None, height: int = None) -> VideoFileClip:
        """
        Resize a video clip while maintaining aspect ratio.
        
        Args:
            video_clip: MoviePy VideoFileClip object
            width: Target width (None to maintain aspect ratio)
            height: Target height (None to maintain aspect ratio)
            
        Returns:
            Resized VideoFileClip
        """
        if width is None and height is None:
            return video_clip
        
        return video_clip.resize(width=width, height=height)
    
    def set_fade_duration(self, duration: float) -> None:
        self.fade_duration = duration