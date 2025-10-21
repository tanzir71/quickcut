"""Settings dialog for Quick Cut video editor."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from config.settings import Settings
from utils.validators import Validators

class SettingsDialog:
    """Settings configuration dialog."""
    
    def __init__(self, parent: tk.Tk, settings: Settings):
        """Initialize settings dialog."""
        self.parent = parent
        self.settings = settings
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # Inherit background color from parent window
        try:
            self.dialog.configure(background=self.parent.cget('bg'))
        except Exception:
            pass
        
        # Ensure theme matches the rest of the UI
        try:
            ttk.Style(self.dialog).theme_use('clam')
        except Exception:
            pass
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.center_dialog()
        
        # Create widgets
        self.create_widgets()
        
        # Load current settings
        self.load_settings()
        
    def center_dialog(self):
        """Center the dialog on parent window."""
        try:
            self.parent.update_idletasks()
        except Exception:
            pass
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = 600
        dialog_height = 500
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def create_widgets(self):
        """Create and layout all widgets."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_general_tab()
        self.create_audio_tab()
        self.create_video_tab()
        self.create_advanced_tab()
        
        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_to_defaults).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="OK", 
                  command=self.ok, style='Accent.TButton').pack(side="right", padx=5)
        
    def create_general_tab(self):
        """Create general settings tab."""
        general_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(general_frame, text="General")
        
        # Output format
        ttk.Label(general_frame, text="Default Output Format:").grid(row=0, column=0, sticky="w", pady=5)
        self.output_format_var = tk.StringVar()
        output_format_combo = ttk.Combobox(general_frame, textvariable=self.output_format_var,
                                          values=[".mp4", ".avi", ".mov", ".mkv"], state="readonly")
        output_format_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Output quality
        ttk.Label(general_frame, text="Output Quality:").grid(row=1, column=0, sticky="w", pady=5)
        self.output_quality_var = tk.StringVar()
        quality_combo = ttk.Combobox(general_frame, textvariable=self.output_quality_var,
                                     values=["High", "Medium", "Low"], state="readonly")
        quality_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Output resolution
        ttk.Label(general_frame, text="Output Resolution:").grid(row=2, column=0, sticky="w", pady=5)
        self.output_resolution_var = tk.StringVar()
        resolution_combo = ttk.Combobox(general_frame, textvariable=self.output_resolution_var,
                                       values=["Original", "1920x1080", "1280x720", "854x480"], state="readonly")
        resolution_combo.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Auto-save settings
        self.auto_save_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="Auto-save settings on exit", 
                       variable=self.auto_save_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # Show confirmation dialogs
        self.confirm_delete_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="Show confirmation before overwriting files", 
                       variable=self.confirm_delete_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
    def create_audio_tab(self):
        """Create audio settings tab."""
        audio_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(audio_frame, text="Audio")
        
        # Silence detection method
        ttk.Label(audio_frame, text="Silence Detection Method:").grid(row=0, column=0, sticky="w", pady=5)
        self.silence_method_var = tk.StringVar()
        method_combo = ttk.Combobox(audio_frame, textvariable=self.silence_method_var,
                                   values=["RMS Energy", "Spectral Centroid", "Zero Crossing Rate"], state="readonly")
        method_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Audio normalization
        self.normalize_audio_var = tk.BooleanVar()
        ttk.Checkbutton(audio_frame, text="Normalize audio output", 
                       variable=self.normalize_audio_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Audio codec
        ttk.Label(audio_frame, text="Audio Codec:").grid(row=2, column=0, sticky="w", pady=5)
        self.audio_codec_var = tk.StringVar()
        codec_combo = ttk.Combobox(audio_frame, textvariable=self.audio_codec_var,
                                  values=["aac", "mp3", "wav", "flac"], state="readonly")
        codec_combo.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Audio bitrate
        ttk.Label(audio_frame, text="Audio Bitrate (kbps):").grid(row=3, column=0, sticky="w", pady=5)
        self.audio_bitrate_var = tk.StringVar()
        bitrate_combo = ttk.Combobox(audio_frame, textvariable=self.audio_bitrate_var,
                                    values=["128", "192", "256", "320"], state="readonly")
        bitrate_combo.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        
    def create_video_tab(self):
        """Create video settings tab."""
        video_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(video_frame, text="Video")
        
        # Video codec
        ttk.Label(video_frame, text="Video Codec:").grid(row=0, column=0, sticky="w", pady=5)
        self.video_codec_var = tk.StringVar()
        codec_combo = ttk.Combobox(video_frame, textvariable=self.video_codec_var,
                                  values=["libx264", "libx265", "mpeg4", "rawvideo"], state="readonly")
        codec_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Video bitrate
        ttk.Label(video_frame, text="Video Bitrate (Mbps):").grid(row=1, column=0, sticky="w", pady=5)
        self.video_bitrate_var = tk.StringVar()
        self.video_bitrate_entry = ttk.Entry(video_frame, textvariable=self.video_bitrate_var, width=10)
        self.video_bitrate_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Frame rate
        ttk.Label(video_frame, text="Frame Rate (fps):").grid(row=2, column=0, sticky="w", pady=5)
        self.frame_rate_var = tk.StringVar()
        self.frame_rate_entry = ttk.Entry(video_frame, textvariable=self.frame_rate_var, width=10)
        self.frame_rate_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Fade transitions
        self.fade_transitions_var = tk.BooleanVar()
        ttk.Checkbutton(video_frame, text="Enable fade transitions", 
                       variable=self.fade_transitions_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # Fade duration
        ttk.Label(video_frame, text="Fade Duration (seconds):").grid(row=4, column=0, sticky="w", pady=5)
        self.fade_duration_var = tk.DoubleVar()
        fade_scale = ttk.Scale(video_frame, from_=0.0, to=2.0, orient="horizontal",
                               variable=self.fade_duration_var, length=200)
        fade_scale.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        self.fade_duration_label = ttk.Label(video_frame, text="0.0s")
        self.fade_duration_label.grid(row=4, column=2, sticky="w", padx=5)
        
        # Update fade duration label
        def update_fade_label(*args):
            self.fade_duration_label.config(text=f"{self.fade_duration_var.get():.1f}s")
        self.fade_duration_var.trace('w', update_fade_label)
        
    def create_advanced_tab(self):
        """Create advanced settings tab."""
        advanced_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Thread count
        ttk.Label(advanced_frame, text="Processing Threads:").grid(row=0, column=0, sticky="w", pady=5)
        self.thread_count_var = tk.StringVar()
        thread_combo = ttk.Combobox(advanced_frame, textvariable=self.thread_count_var,
                                    values=["1", "2", "4", "8", "16"], state="readonly", width=5)
        thread_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Buffer size
        ttk.Label(advanced_frame, text="Audio Buffer Size:").grid(row=1, column=0, sticky="w", pady=5)
        self.buffer_size_var = tk.StringVar()
        buffer_combo = ttk.Combobox(advanced_frame, textvariable=self.buffer_size_var,
                                  values=["1024", "2048", "4096", "8192"], state="readonly", width=8)
        buffer_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Temporary directory
        ttk.Label(advanced_frame, text="Temporary Directory:").grid(row=2, column=0, sticky="w", pady=5)
        self.temp_dir_var = tk.StringVar()
        temp_entry = ttk.Entry(advanced_frame, textvariable=self.temp_dir_var, width=40)
        temp_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(advanced_frame, text="Browse...", command=self.browse_temp_dir).grid(row=2, column=2, padx=5)
        
        # Log level
        ttk.Label(advanced_frame, text="Log Level:").grid(row=3, column=0, sticky="w", pady=5)
        self.log_level_var = tk.StringVar()
        log_combo = ttk.Combobox(advanced_frame, textvariable=self.log_level_var,
                               values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly")
        log_combo.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # Enable debug mode
        self.debug_mode_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Enable debug mode", 
                       variable=self.debug_mode_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
    def browse_temp_dir(self):
        """Browse for temporary directory."""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Select Temporary Directory", parent=self.dialog)
        if directory:
            self.temp_dir_var.set(directory)
            
    def load_settings(self):
        """Load current settings into the dialog."""
        # General tab
        self.output_format_var.set(self.settings.get('output_format', '.mp4'))
        self.output_quality_var.set(self.settings.get('output_quality', 'High'))
        self.output_resolution_var.set(self.settings.get('output_resolution', 'Original'))
        self.auto_save_var.set(self.settings.get('auto_save_settings', True))
        self.confirm_delete_var.set(self.settings.get('confirm_overwrite', True))
        
        # Audio tab
        self.silence_method_var.set(self.settings.get('silence_detection_method', 'RMS Energy'))
        self.normalize_audio_var.set(self.settings.get('normalize_audio', False))
        self.audio_codec_var.set(self.settings.get('audio_codec', 'aac'))
        self.audio_bitrate_var.set(str(self.settings.get('audio_bitrate', 192)))
        
        # Video tab
        self.video_codec_var.set(self.settings.get('video_codec', 'libx264'))
        self.video_bitrate_var.set(str(self.settings.get('video_bitrate', 8)))
        self.frame_rate_var.set(str(self.settings.get('frame_rate', 30)))
        self.fade_transitions_var.set(self.settings.get('enable_fade_transitions', True))
        self.fade_duration_var.set(self.settings.get('fade_duration', 0.5))
        
        # Advanced tab
        self.thread_count_var.set(str(self.settings.get('processing_threads', 4)))
        self.buffer_size_var.set(str(self.settings.get('audio_buffer_size', 2048)))
        self.temp_dir_var.set(self.settings.get('temp_directory', ''))
        self.log_level_var.set(self.settings.get('log_level', 'INFO'))
        self.debug_mode_var.set(self.settings.get('debug_mode', False))
        
    def validate_settings(self) -> bool:
        """Validate all settings."""
        try:
            # Validate numeric fields
            video_bitrate = float(self.video_bitrate_var.get())
            if not Validators.is_positive_number(str(video_bitrate)):
                messagebox.showerror("Invalid Setting", "Video bitrate must be a positive number.")
                return False
                
            frame_rate = float(self.frame_rate_var.get())
            if not Validators.is_positive_number(str(frame_rate)):
                messagebox.showerror("Invalid Setting", "Frame rate must be a positive number.")
                return False
                
            fade_duration = self.fade_duration_var.get()
            if not Validators.is_valid_fade_duration(fade_duration):
                messagebox.showerror("Invalid Setting", "Fade duration must be between 0.0 and 2.0 seconds.")
                return False
                
            # Validate temporary directory
            temp_dir = self.temp_dir_var.get()
            if temp_dir and not Validators.is_valid_directory_path(temp_dir):
                messagebox.showerror("Invalid Setting", "Temporary directory path is invalid.")
                return False
                
            return True
            
        except ValueError as e:
            messagebox.showerror("Invalid Setting", f"Invalid numeric value: {e}")
            return False
            
    def save_settings(self):
        """Save settings to the settings object."""
        # General tab
        self.settings.set('output_format', self.output_format_var.get())
        self.settings.set('output_quality', self.output_quality_var.get())
        self.settings.set('output_resolution', self.output_resolution_var.get())
        self.settings.set('auto_save_settings', self.auto_save_var.get())
        self.settings.set('confirm_overwrite', self.confirm_delete_var.get())
        
        # Audio tab
        self.settings.set('silence_detection_method', self.silence_method_var.get())
        self.settings.set('normalize_audio', self.normalize_audio_var.get())
        self.settings.set('audio_codec', self.audio_codec_var.get())
        self.settings.set('audio_bitrate', int(self.audio_bitrate_var.get()))
        
        # Video tab
        self.settings.set('video_codec', self.video_codec_var.get())
        self.settings.set('video_bitrate', float(self.video_bitrate_var.get()))
        self.settings.set('frame_rate', float(self.frame_rate_var.get()))
        self.settings.set('enable_fade_transitions', self.fade_transitions_var.get())
        self.settings.set('fade_duration', self.fade_duration_var.get())
        
        # Advanced tab
        self.settings.set('processing_threads', int(self.thread_count_var.get()))
        self.settings.set('audio_buffer_size', int(self.buffer_size_var.get()))
        self.settings.set('temp_directory', self.temp_dir_var.get())
        self.settings.set('log_level', self.log_level_var.get())
        self.settings.set('debug_mode', self.debug_mode_var.get())
        
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to their default values?"):
            self.settings.reset_to_defaults()
            self.load_settings()
            messagebox.showinfo("Settings Reset", "All settings have been reset to their default values.")
            
    def ok(self):
        """Handle OK button click."""
        if self.validate_settings():
            self.save_settings()
            self.settings.save()
            self.dialog.destroy()
            
    def cancel(self):
        """Handle Cancel button click."""
        self.dialog.destroy()