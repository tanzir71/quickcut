"""Main GUI window for Quick Cut video editor."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path

from processor.video_processor import VideoProcessor
from config.settings import Settings
from utils.file_utils import FileUtils
from utils.validators import Validators

class MainWindow:
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Quick Cut - Video Silence Remover")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        # Center window on screen
        self.center_window()
        
        # Initialize components
        self.settings = Settings()
        self.video_processor = None
        self.current_file = None
        self.is_processing = False
        
        # Configure styles
        self.setup_styles()
        
        # Create widgets
        self.create_widgets()
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def setup_styles(self):
        """Setup application styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Set global background color to match internal content
        bg_color = '#DCDAD5'
        try:
            self.root.configure(bg=bg_color)
        except Exception:
            pass
        
        # Base widget backgrounds
        style.configure('TFrame', background=bg_color)
        style.configure('TLabelframe', background=bg_color)
        style.configure('TLabelframe.Label', background=bg_color)
        style.configure('TLabel', background=bg_color)
        style.configure('TCheckbutton', background=bg_color)
        style.configure('TNotebook', background=bg_color)
        style.configure('TNotebook.Tab', background=bg_color)
        
        # Configure button styles
        style.configure('Accent.TButton', 
                       background='#007acc', 
                       foreground='white',
                       borderwidth=1,
                       focusthickness=3,
                       focuscolor='#007acc')
        style.map('Accent.TButton',
                 background=[('active', '#005a9e'), ('disabled', '#cccccc')])
        
        style.configure('Success.TButton',
                       background='#28a745',
                       foreground='white',
                       borderwidth=1)
        style.map('Success.TButton',
                 background=[('active', '#218838')])
        
        # Configure progress bar style
        style.configure('Horizontal.TProgressbar',
                       background='#007acc',
                       troughcolor=bg_color,
                       borderwidth=1,
                       lightcolor='#007acc',
                       darkcolor='#007acc')
        
        # Configure scale trough to blend with background
        style.configure('TScale', troughcolor=bg_color)
        
        # Status bar label style
        style.configure('Status.TLabel', background=bg_color)
        
    def create_widgets(self):
        """Create and layout all widgets."""
        # File selection frame
        self.create_file_frame()
        
        # Settings frame
        self.create_settings_frame()
        
        # Progress frame
        self.create_progress_frame()
        
        # Control buttons frame
        self.create_control_frame()
        
        # Status bar
        self.create_status_bar()
        
    def create_file_frame(self):
        """Create file selection frame."""
        file_frame = ttk.LabelFrame(self.root, text="Input Video", padding="10")
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)
        
        # Input file
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky="w", padx=5)
        self.input_file_var = tk.StringVar()
        self.input_entry = ttk.Entry(file_frame, textvariable=self.input_file_var, state="readonly")
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Button(file_frame, text="Browse...", command=self.browse_input_file).grid(row=0, column=2, padx=5)
        
        # Output file
        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky="w", padx=5, pady=(5, 0))
        self.output_file_var = tk.StringVar()
        self.output_entry = ttk.Entry(file_frame, textvariable=self.output_file_var)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))
        
        ttk.Button(file_frame, text="Browse...", command=self.browse_output_file).grid(row=1, column=2, padx=5, pady=(5, 0))
        
        # Auto-generate output filename
        self.auto_output_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Auto-generate output filename", 
                       variable=self.auto_output_var, 
                       command=self.toggle_auto_output).grid(row=2, column=1, sticky="w", padx=5, pady=(5, 0))
        
    def create_settings_frame(self):
        """Create settings frame."""
        settings_frame = ttk.LabelFrame(self.root, text="Processing Settings", padding="10")
        settings_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Silence threshold
        ttk.Label(settings_frame, text="Silence Threshold (dB):").grid(row=0, column=0, sticky="w", padx=5)
        self.threshold_var = tk.DoubleVar(value=self.settings.get('silence_threshold'))
        threshold_scale = ttk.Scale(settings_frame, from_=-60, to=-20, orient="horizontal",
                                   variable=self.threshold_var,
                                   command=self.update_threshold_display)
        threshold_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.threshold_label = ttk.Label(settings_frame, text=f"{self.threshold_var.get():.1f} dB")
        self.threshold_label.grid(row=0, column=2, padx=5)
        
        # Minimum silence duration
        ttk.Label(settings_frame, text="Min Silence Duration (s):").grid(row=1, column=0, sticky="w", padx=5, pady=(5, 0))
        self.min_silence_var = tk.DoubleVar(value=self.settings.get('min_silence_duration'))
        min_silence_scale = ttk.Scale(settings_frame, from_=0.1, to=5.0, orient="horizontal",
                                     variable=self.min_silence_var,
                                     command=self.update_min_silence_display)
        min_silence_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=(5, 0))
        self.min_silence_label = ttk.Label(settings_frame, text=f"{self.min_silence_var.get():.1f}s")
        self.min_silence_label.grid(row=1, column=2, padx=5, pady=(5, 0))
        
        # Fade duration
        ttk.Label(settings_frame, text="Fade Duration (s):").grid(row=2, column=0, sticky="w", padx=5, pady=(5, 0))
        self.fade_duration_var = tk.DoubleVar(value=self.settings.get('fade_duration'))
        fade_scale = ttk.Scale(settings_frame, from_=0.0, to=1.0, orient="horizontal",
                              variable=self.fade_duration_var,
                              command=self.update_fade_display)
        fade_scale.grid(row=2, column=1, sticky="ew", padx=5, pady=(5, 0))
        self.fade_label = ttk.Label(settings_frame, text=f"{self.fade_duration_var.get():.1f}s")
        self.fade_label.grid(row=2, column=2, padx=5, pady=(5, 0))
        
        # Additional options
        self.normalize_var = tk.BooleanVar(value=self.settings.get('enable_audio_normalization', True))
        ttk.Checkbutton(settings_frame, text="Normalize audio", 
                       variable=self.normalize_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 0))
        
        self.keep_original_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Keep original video quality", 
                        variable=self.keep_original_var).grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 0))
        
    def create_progress_frame(self):
        """Create progress frame."""
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding="10")
        progress_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Progress text
        self.progress_text_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_text_var)
        self.progress_label.grid(row=1, column=0, sticky="w")
        
        # Time remaining
        self.time_remaining_var = tk.StringVar(value="")
        self.time_label = ttk.Label(progress_frame, textvariable=self.time_remaining_var)
        self.time_label.grid(row=1, column=0, sticky="e")
        
    def create_control_frame(self):
        """Create control buttons frame."""
        control_frame = ttk.Frame(self.root)
        control_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        # Left buttons
        left_frame = ttk.Frame(control_frame)
        left_frame.pack(side="left")
        
        ttk.Button(left_frame, text="Settings...", command=self.show_settings).pack(side="left", padx=5)
        ttk.Button(left_frame, text="About", command=self.show_about).pack(side="left", padx=5)
        
        # Right buttons
        right_frame = ttk.Frame(control_frame)
        right_frame.pack(side="right")
        
        self.process_button = ttk.Button(right_frame, text="Process Video", 
                                        command=self.process_video, style='Accent.TButton')
        self.process_button.pack(side="left", padx=5)
        
        self.cancel_button = ttk.Button(right_frame, text="Cancel", 
                                         command=self.cancel_processing, state="disabled")
        self.cancel_button.pack(side="left", padx=5)
        
    def create_status_bar(self):
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", style='Status.TLabel')
        status_bar.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        
    def update_threshold_display(self, value):
        """Update threshold label."""
        self.threshold_label.config(text=f"{float(value):.1f} dB")
        
    def update_min_silence_display(self, value):
        """Update minimum silence label."""
        self.min_silence_label.config(text=f"{float(value):.1f}s")
        
    def update_fade_display(self, value):
        """Update fade label."""
        self.fade_label.config(text=f"{float(value):.1f}s")
        
    def toggle_auto_output(self):
        """Toggle auto output filename generation."""
        if self.auto_output_var.get() and self.current_file:
            self.generate_output_filename()
        
    def center_window(self):
        """Center main window on the screen."""
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
        
    def browse_input_file(self):
        """Browse for input video file."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Input Video File",
            filetypes=filetypes,
            initialdir=self.settings.get('last_input_dir', os.getcwd()),
            parent=self.root
        )
        
        if filename:
            if Validators.is_valid_video_file(filename, self.settings.get('supported_formats')):
                self.current_file = filename
                self.input_file_var.set(filename)
                self.settings.set('last_input_dir', os.path.dirname(filename))
                
                if self.auto_output_var.get():
                    self.generate_output_filename()
                
                self.update_status(f"Selected: {os.path.basename(filename)}")
            else:
                messagebox.showerror("Invalid File", "Please select a valid video file.", parent=self.root)
                
    def browse_output_file(self):
        """Browse for output file."""
        if not self.current_file:
            messagebox.showwarning("No Input File", "Please select an input file first.", parent=self.root)
            return
            
        filetypes = [
            ("MP4 files", "*.mp4"),
            ("AVI files", "*.avi"),
            ("All files", "*.*")
        ]
        
        initial_dir = self.settings.get('last_output_dir', os.path.dirname(self.current_file))
        
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            filetypes=filetypes,
            initialdir=initial_dir,
            defaultextension=".mp4",
            initialfile=os.path.splitext(os.path.basename(self.current_file))[0] + "_cut.mp4",
            parent=self.root
        )
        
        if filename:
            self.output_file_var.set(filename)
            self.settings.set('last_output_dir', os.path.dirname(filename))
            
    def generate_output_filename(self):
        """Auto-generate output filename."""
        if not self.current_file:
            return
            
        base_name = os.path.splitext(os.path.basename(self.current_file))[0]
        output_dir = os.path.dirname(self.current_file)
        
        # Generate unique filename
        counter = 1
        while True:
            output_name = f"{base_name}_cut_{counter}.mp4"
            output_path = os.path.join(output_dir, output_name)
            
            if not os.path.exists(output_path):
                self.output_file_var.set(output_path)
                break
                
            counter += 1
            
            # Safety limit
            if counter > 1000:
                self.output_file_var.set(os.path.join(output_dir, f"{base_name}_cut.mp4"))
                break
                
    def show_settings(self):
        """Show settings dialog."""
        from .settings_dialog import SettingsDialog
        SettingsDialog(self.root, self.settings)
        
    def show_about(self):
        """Show about dialog."""
        about_text = """Quick Cut - Video Silence Remover

Version 1.0.0

A minimal video editor that automatically removes silent sections from videos.

Features:
• Automatic silence detection
• Configurable threshold and duration
• Smooth fade transitions
• Multiple output formats
• Progress tracking

Built with Python, Tkinter, MoviePy, and Librosa."""
        
        messagebox.showinfo("About Quick Cut", about_text, parent=self.root)
        
    def process_video(self):
        """Start video processing."""
        if not self.current_file:
            messagebox.showwarning("No Input File", "Please select an input video file.", parent=self.root)
            return
            
        output_file = self.output_file_var.get().strip()
        if not output_file:
            messagebox.showwarning("No Output File", "Please specify an output file.", parent=self.root)
            return
            
        if not Validators.is_valid_output_path(output_file):
            messagebox.showerror("Invalid Output Path", "Please select a valid output file path.", parent=self.root)
            return
            
        # Check if output file exists
        if os.path.exists(output_file):
            if not messagebox.askyesno("File Exists", 
                                      f"The file '{os.path.basename(output_file)}' already exists.\n\nDo you want to replace it?",
                                      parent=self.root):
                return
                
        # Save current settings
        self.save_current_settings()
        
        # Disable controls
        self.set_controls_state("disabled")
        self.is_processing = True
        self.progress_var.set(0)
        self.progress_text_var.set("Initializing...")
        self.time_remaining_var.set("")
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_video_thread, args=(output_file,))
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def process_video_thread(self, output_file: str):
        """Process video in separate thread."""
        try:
            # Create video processor with current settings
            self.video_processor = VideoProcessor(
                silence_threshold=self.threshold_var.get(),
                min_silence_duration=self.min_silence_var.get(),
                fade_duration=self.fade_duration_var.get(),
                progress_callback=self.update_progress
            )
            
            
            # Process video
            success = self.video_processor.process_video(
                input_path=self.current_file,
                output_path=output_file,
                enable_fade_transitions=True,
                enable_audio_normalization=self.normalize_var.get()
            )
            
            if success:
                self.root.after(0, self.processing_complete, output_file)
            else:
                self.root.after(0, self.processing_failed, "Processing failed")
                
        except Exception as e:
            self.root.after(0, self.processing_failed, str(e))
            
    def update_progress(self, progress: float, status: str = "", time_remaining: str = ""):
        """Update progress display."""
        self.root.after(0, self._update_progress_gui, progress, status, time_remaining)
        
    def _update_progress_gui(self, progress: float, status: str, time_remaining: str):
        """Update progress GUI (called from main thread)."""
        self.progress_var.set(progress)
        if status:
            self.progress_text_var.set(status)
        if time_remaining:
            self.time_remaining_var.set(f"Time remaining: {time_remaining}")
        else:
            self.time_remaining_var.set("")
            
    def processing_complete(self, output_file: str):
        """Handle processing completion."""
        self.is_processing = False
        self.set_controls_state("normal")
        self.progress_var.set(100)
        self.progress_text_var.set("Processing complete!")
        self.time_remaining_var.set("")
        
        # Show completion dialog
        file_size = FileUtils.format_file_size(os.path.getsize(output_file))
        result = messagebox.askyesno("Processing Complete", 
                                    f"Video processing completed successfully!\n\n"
                                    f"Output file: {os.path.basename(output_file)}\n"
                                    f"File size: {file_size}\n\n"
                                    f"Do you want to open the output folder?",
                                    parent=self.root)
        
        if result:
            FileUtils.open_file_location(output_file)
            
    def processing_failed(self, error_message: str):
        """Handle processing failure."""
        self.is_processing = False
        self.set_controls_state("normal")
        self.progress_var.set(0)
        self.progress_text_var.set("Processing failed")
        self.time_remaining_var.set("")
        
        messagebox.showerror("Processing Failed", 
                            f"Video processing failed with the following error:\n\n{error_message}",
                            parent=self.root)
        
    def cancel_processing(self):
        """Cancel current processing."""
        if self.is_processing and self.video_processor:
            if messagebox.askyesno("Cancel Processing", 
                                  "Are you sure you want to cancel the current processing?",
                                  parent=self.root):
                self.video_processor.cancel()
                self.is_processing = False
                self.set_controls_state("normal")
                self.progress_var.set(0)
                self.progress_text_var.set("Processing cancelled")
                self.time_remaining_var.set("")
                
    def set_controls_state(self, state: str):
        """Enable/disable controls during processing."""
        # File controls
        self.input_entry.config(state="readonly" if state == "normal" else "disabled")
        self.output_entry.config(state=state)
        
        # Settings controls
        for child in self.root.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child['text'] == "Processing Settings":
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Scale, ttk.Checkbutton)):
                        widget.config(state=state)
                        
        # Control buttons
        self.process_button.config(state=state)
        self.cancel_button.config(state="normal" if state == "disabled" else "disabled")
        
    def save_current_settings(self):
        """Save current settings."""
        self.settings.set('silence_threshold', self.threshold_var.get())
        self.settings.set('min_silence_duration', self.min_silence_var.get())
        self.settings.set('fade_duration', self.fade_duration_var.get())
        self.settings.set('enable_audio_normalization', self.normalize_var.get())
        self.settings.save()
        
    def update_status(self, message: str):
        """Update status bar."""
        self.status_var.set(message)
        
    def run(self):
        """Run the application."""
        self.root.mainloop()