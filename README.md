# Quick Cut - Video Silence Remover

A minimal Python video editor that automatically removes silent sections from videos. Perfect for creating engaging content by cutting out pauses, dead air, and silent moments.

## Features

- **Automatic Silence Detection**: Uses advanced audio analysis to detect silent sections
- **Configurable Parameters**: Adjust silence threshold, minimum duration, and fade transitions
- **Multiple Output Formats**: Support for MP4, AVI, MOV, MKV, and more
- **Progress Tracking**: Real-time progress bar with time remaining estimates
- **Cross-Platform GUI**: User-friendly interface built with Tkinter
- **Audio Normalization**: Optional audio normalization for consistent volume levels
- **Smooth Transitions**: Configurable fade transitions between segments
- **Memory Efficient**: Optimized for processing large video files

## Installation

1. **Install Python 3.7+** (if not already installed)

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **ASR Model Setup (Required, auto-download enabled)**:
   - If no model is configured, Quick Cut auto-downloads the default English model (`vosk-model-small-en-us-0.15`) into `models/` on first run.
   - To use a different model, place it under `models/` or set `VOSK_MODEL` to the full model directory path.
   - If the download fails (offline or blocked), manually download a Vosk model and configure `VOSK_MODEL`; otherwise processing fails with an ASR error.

4. **Run the Application**:
   ```bash
   python main.py
   ```

## Usage

### Basic Usage

1. **Launch the Application**: Run `python main.py`

2. **Select Input Video**: Click "Browse..." to select your video file

3. **Configure Settings**: Adjust silence detection parameters:
   - **Silence Threshold**: How quiet is considered silence (-60 to -20 dB)
   - **Minimum Silence Duration**: How long silence must last to be removed (0.1 to 5.0 seconds)
   - **Fade Duration**: Smooth transition duration between segments (0.0 to 1.0 seconds)

4. **Choose Output**: The application will auto-generate an output filename, or you can specify your own

5. **Process Video**: Click "Process Video" to start the silence removal

### Advanced Settings

Access the Settings dialog for advanced options:
- Output format and quality settings
- Audio and video codec configuration
- Processing thread count
- Temporary directory settings
- Debug mode options

## Technical Details

### Architecture

The application consists of several key modules:

- **`main.py`**: Application entry point and GUI initialization
- **`gui/main_window.py`**: Main application window with file selection and progress tracking
- **`gui/settings_dialog.py`**: Configuration dialog for advanced settings
- **`processor/audio_analyzer.py`**: Audio analysis for silence detection using Librosa
- **`processor/video_processor.py`**: Core video processing engine
- **`processor/video_editor.py`**: Video editing utilities using MoviePy
- **`config/settings.py`**: Configuration management
- **`utils/file_utils.py`**: File operation utilities
- **`utils/validators.py`**: Input validation utilities

### Silence Detection Algorithm

The application uses multiple audio analysis techniques:

1. **RMS Energy Analysis**: Calculates root mean square energy levels
2. **Spectral Analysis**: Analyzes frequency content to distinguish speech from silence
3. **Zero Crossing Rate**: Measures frequency characteristics of audio signals
4. **ASR Word Timestamps (required)**: Recognized word timestamps drive speech segmentation. Filler tokens detected by ASR are subtracted from speech ranges for cleaner cuts. Processing requires a configured Vosk model.

### Processing Pipeline

1. **Audio Extraction**: Extract audio track from video file
2. **ASR Speech Detection**: Use offline ASR (Vosk) word timestamps to identify speech segments
3. **Filler Removal**: Subtract ASR-detected filler words from speech segments
4. **Video Processing**: Extract and concatenate video segments
5. **Audio Processing**: Apply normalization and transitions
6. **Output Generation**: Create final video file with removed silence

## Supported Formats

### Input Formats
- MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V
- Most video formats supported by MoviePy

### Output Formats
- MP4 (default), AVI, MOV, MKV
- Configurable video and audio codecs

## Configuration

### Default Settings

- **Silence Threshold**: -40 dB
- **Minimum Silence Duration**: 0.5 seconds
- **Fade Duration**: 0.1 seconds
- **Audio Normalization**: Disabled
- **Output Format**: MP4
- **Video Quality**: High

### Settings Storage

Settings are stored in a JSON file in the user's home directory:
- **Windows**: `%USERPROFILE%\.quick_cut\settings.json`
- **macOS/Linux**: `~/.quick_cut/settings.json`

## Performance Tips

1. **For Large Files**: Increase processing threads in advanced settings
2. **For Better Quality**: Use higher output quality settings
3. **For Faster Processing**: Reduce fade duration or disable normalization
4. **Memory Management**: Use temporary directory on fast storage (SSD recommended)

## Troubleshooting

### Common Issues

**"Error importing required modules"**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.7+ required)

**"Processing failed"**
- Check input file format compatibility
- Verify sufficient disk space for output
- Try reducing output quality for large files

**"ASR model not available"**
- The app attempts to auto-download the default English model. If you're offline or the download is blocked, manually download a Vosk model and set `VOSK_MODEL` to its directory, or place the model under `models/`.

**"Permission denied"**
- Run with appropriate permissions
- Check output directory write permissions

**"Out of memory"**
- Reduce processing thread count
- Use lower quality settings
- Process smaller video segments

### Debug Mode

Enable debug mode in Settings for detailed logging and troubleshooting information.

## Contributing

This is a minimal implementation focused on core functionality. Contributions are welcome for:
- Additional audio analysis algorithms
- Support for more video formats
- Performance optimizations
- User interface improvements
- Additional transition effects

## License

This project is open source and available under the MIT License.

## Dependencies

- **moviepy**: Video editing and processing
- **pydub**: Audio manipulation
- **librosa**: Audio analysis and feature extraction
- **numpy**: Numerical computing
- **imageio-ffmpeg**: FFmpeg wrapper for video I/O
- **tkinter**: GUI framework (included with Python)
- **vosk**: Offline ASR engine (required)

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.7 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: Sufficient space for input and output files
- **Processor**: Multi-core processor recommended

---

**Quick Cut** - Making video editing simple and efficient by automatically removing unwanted silence.

## ASR Requirements

Quick Cut requires an offline ASR model.

- Install dependencies: `pip install -r requirements.txt` (includes `vosk`).
- If no model is configured, Quick Cut auto-downloads the default English model (`vosk-model-small-en-us-0.15`) into `models/`. To use another model, set `VOSK_MODEL` to its directory or place it under `models/`.
- Processing fails with a clear error if auto-download fails or the model is misconfigured.

### Notes
- ASR runs fully offline and works on Windows.
- Audio-only fades are applied between micro-cuts to avoid black frames.