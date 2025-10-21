"""
Configuration management for Quick Cut video editor.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Settings:
    """Manages application settings and configuration."""
    
    def __init__(self):
        """Initialize settings with default values."""
        self.config_file = Path.home() / '.quick-cut' / 'config.json'
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Default settings
        self.defaults = {
            'silence_threshold': -40.0,  # dB
            'min_silence_duration': 2.0,  # seconds
            
            'fade_duration': 0.1,  # seconds
            'output_format': 'mp4',
            'output_quality': 'medium',
            'output_resolution': 'original',
            'enable_audio_normalization': True,
            'enable_fade_transitions': True,
            'last_output_directory': str(Path.home() / 'Desktop'),
            'supported_formats': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        }
        
        self.current = self.defaults.copy()
        self.load()
    
    def load(self) -> None:
        """Load settings from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.current.update(loaded)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")
            self.current = self.defaults.copy()
    
    def save(self) -> None:
        """Save current settings to configuration file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.current, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.current.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.current[key] = value
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self.current = self.defaults.copy()
    
    def get_silence_threshold(self) -> float:
        """Get silence threshold in dB."""
        return float(self.get('silence_threshold', -40.0))
    
    def set_silence_threshold(self, value: float) -> None:
        """Set silence threshold in dB."""
        self.set('silence_threshold', float(value))
    
    def get_min_silence_duration(self) -> float:
        """Get minimum silence duration in seconds."""
        return float(self.get('min_silence_duration', 0.5))
    
    def set_min_silence_duration(self, value: float) -> None:
        """Set minimum silence duration in seconds."""
        self.set('min_silence_duration', float(value))
    
    
    
    def get_fade_duration(self) -> float:
        """Get fade duration in seconds."""
        return float(self.get('fade_duration', 0.1))
    
    def set_fade_duration(self, value: float) -> None:
        """Set fade duration in seconds."""
        self.set('fade_duration', float(value))
    
    def get_output_format(self) -> str:
        """Get output video format."""
        return self.get('output_format', 'mp4').lower()
    
    def set_output_format(self, format: str) -> None:
        """Set output video format."""
        self.set('output_format', format.lower())
    
    def get_output_quality(self) -> str:
        """Get output video quality."""
        return self.get('output_quality', 'medium').lower()
    
    def set_output_quality(self, quality: str) -> None:
        """Set output video quality."""
        self.set('output_quality', quality.lower())
    
    def get_output_resolution(self) -> str:
        """Get output video resolution."""
        return self.get('output_resolution', 'original').lower()
    
    def set_output_resolution(self, resolution: str) -> None:
        """Set output video resolution."""
        self.set('output_resolution', resolution.lower())
    
    def is_audio_normalization_enabled(self) -> bool:
        """Check if audio normalization is enabled."""
        return bool(self.get('enable_audio_normalization', True))
    
    def set_audio_normalization_enabled(self, enabled: bool) -> None:
        """Enable/disable audio normalization."""
        self.set('enable_audio_normalization', bool(enabled))
    
    def is_fade_transitions_enabled(self) -> bool:
        """Check if fade transitions are enabled."""
        return bool(self.get('enable_fade_transitions', True))
    
    def set_fade_transitions_enabled(self, enabled: bool) -> None:
        """Enable/disable fade transitions."""
        self.set('enable_fade_transitions', bool(enabled))
    
    def get_last_output_directory(self) -> str:
        """Get last used output directory."""
        return self.get('last_output_directory', str(Path.home() / 'Desktop'))
    
    def set_last_output_directory(self, directory: str) -> None:
        """Set last used output directory."""
        self.set('last_output_directory', directory)
    
    def get_supported_formats(self) -> list:
        """Get list of supported video formats."""
        return self.get('supported_formats', ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'])
    
    def is_format_supported(self, file_path: str) -> bool:
        """Check if a file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.get_supported_formats()