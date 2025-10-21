"""Utility functions for file operations."""

import os
import shutil
from pathlib import Path
from typing import Optional, List
import sys
import subprocess
import webbrowser
import tempfile

class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def get_duration_string(seconds: float) -> str:
        """Convert seconds to human readable duration string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}h {minutes}m {secs}s"
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """Ensure directory exists, create if necessary."""
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False
    
    @staticmethod
    def get_unique_filename(file_path: str) -> str:
        """Generate a unique filename if the original already exists."""
        if not os.path.exists(file_path):
            return file_path
        
        base_path = Path(file_path)
        directory = base_path.parent
        name = base_path.stem
        extension = base_path.suffix
        
        counter = 1
        while True:
            new_path = directory / f"{name}_{counter}{extension}"
            if not new_path.exists():
                return str(new_path)
            counter += 1
    
    @staticmethod
    def delete_file_safely(file_path: str) -> bool:
        """Safely delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except OSError:
            return False
    
    @staticmethod
    def copy_file_safely(source_path: str, dest_path: str) -> bool:
        """Safely copy a file."""
        try:
            shutil.copy2(source_path, dest_path)
            return True
        except (OSError, shutil.Error):
            return False
    
    @staticmethod
    def get_temp_directory() -> str:
        """Get system temporary directory."""
        return tempfile.gettempdir()
    
    @staticmethod
    def create_temp_file(suffix: str = "") -> str:
        """Create a temporary file and return its path."""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path
    
    @staticmethod
    def list_video_files(directory: str, supported_extensions: List[str]) -> List[str]:
        """List all video files in a directory."""
        video_files = []
        
        try:
            for file in Path(directory).iterdir():
                if file.is_file() and file.suffix.lower() in supported_extensions:
                    video_files.append(str(file))
        except OSError:
            pass
        
        return sorted(video_files)
    
    @staticmethod
    def get_file_modification_time(file_path: str) -> float:
        """Get file modification time as timestamp."""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0.0
    
    @staticmethod
    def is_file_accessible(file_path: str) -> bool:
        """Check if file is accessible for reading."""
        try:
            return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
        except OSError:
            return False
    
    @staticmethod
    def open_file_location(file_path: str) -> bool:
        """Open folder containing the file and highlight it when possible."""
        try:
            if not file_path:
                return False
            full_path = os.path.abspath(file_path)
            if os.name == 'nt':
                # Windows: select the file in Explorer
                try:
                    subprocess.run(['explorer', '/select,', full_path], check=False)
                except Exception:
                    directory = os.path.dirname(full_path)
                    os.startfile(directory)
                return True
            elif sys.platform == 'darwin':
                # macOS: reveal in Finder
                subprocess.run(['open', '-R', full_path], check=False)
                return True
            else:
                # Linux/Unix: open containing directory
                directory = os.path.dirname(full_path) or '.'
                subprocess.run(['xdg-open', directory], check=False)
                return True
        except Exception:
            # Fallback: try opening directory via webbrowser
            try:
                directory = os.path.dirname(os.path.abspath(file_path))
                webbrowser.open(f'file://{directory}')
                return True
            except Exception:
                return False