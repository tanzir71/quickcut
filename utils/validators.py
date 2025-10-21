"""Input validation utilities."""

import os
import re
from pathlib import Path
from typing import Optional, List

class Validators:
    """Input validation utilities."""
    
    @staticmethod
    def is_valid_video_file(file_path: str, supported_formats: List[str]) -> bool:
        """Check if file is a valid video file."""
        if not file_path or not os.path.isfile(file_path):
            return False
        
        file_extension = Path(file_path).suffix.lower()
        return file_extension in [fmt.lower() for fmt in supported_formats]
    
    @staticmethod
    def is_valid_output_path(output_path: str) -> bool:
        """Check if output path is valid."""
        if not output_path:
            return False
        
        try:
            # Check if directory is writable
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                # Try to create directory
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to the directory
            test_file = output_dir / '.test_write'
            test_file.touch()
            test_file.unlink()
            
            return True
        except (OSError, PermissionError):
            return False
    
    @staticmethod
    def is_valid_silence_threshold(threshold: float) -> bool:
        """Check if silence threshold is valid."""
        return -60.0 <= threshold <= -20.0
    
    @staticmethod
    def is_valid_silence_duration(duration: float) -> bool:
        """Check if silence duration is valid."""
        return 0.1 <= duration <= 5.0
    
    @staticmethod
    def is_valid_fade_duration(duration: float) -> bool:
        """Check if fade duration is valid."""
        return 0.0 <= duration <= 1.0
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        # Remove invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = 'output'
        
        return sanitized
    
    @staticmethod
    def is_positive_number(value: str, allow_zero: bool = False) -> bool:
        """Check if string represents a positive number."""
        try:
            num = float(value)
            return num >= 0 if allow_zero else num > 0
        except ValueError:
            return False
    
    @staticmethod
    def is_integer(value: str) -> bool:
        """Check if string represents an integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_directory_path(path: str) -> bool:
        """Check if path is a valid directory."""
        try:
            return Path(path).is_dir()
        except OSError:
            return False
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 2048) -> bool:
        """Check if file size is within limits."""
        try:
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            return file_size <= max_size_bytes
        except OSError:
            return False
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension in lowercase."""
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def is_supported_output_format(format_str: str, supported_formats: List[str]) -> bool:
        """Check if output format is supported."""
        if not format_str:
            return False
        
        format_lower = format_str.lower()
        # Remove leading dot if present
        if format_lower.startswith('.'):
            format_lower = format_lower[1:]
        
        # Add dot for comparison
        format_with_dot = f'.{format_lower}'
        
        return format_with_dot in [fmt.lower() for fmt in supported_formats]