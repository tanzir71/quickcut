import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from processor.video_processor import VideoProcessor


def main():
    inp = 'voice_tray.mp4'
    out = 'voice_tray_cut.mp4'

    print('[ENV] VOSK_MODEL =', os.environ.get('VOSK_MODEL'))
    print('[FS] models dir exists:', Path(ROOT / 'models').exists())
    for cand in ['models/vosk-model-small-en-us-0.15', 'models/vosk-model-en-us-0.22']:
        print('[FS] candidate model path:', cand, '->', Path(ROOT / cand).is_dir())

    try:
        import vosk
        print('[CHECK] vosk imported:', True, 'version:', getattr(vosk, '__version__', 'unknown'))
    except Exception as e:
        print('[CHECK] vosk import failed:', e)

    print('[TEST] Input exists:', Path(ROOT / inp).is_file())

    vp = VideoProcessor(silence_threshold=-40.0, min_silence_duration=2.0, fade_duration=0.2)
    try:
        print('[RUN] Starting processing...')
        ok = vp.process_video(str(ROOT / inp), str(ROOT / out), enable_fade_transitions=True, enable_audio_normalization=True)
        print('[RUN] Completed. ok =', ok)
        out_path = ROOT / out
        if ok and out_path.is_file():
            print('[OUT] Output path:', str(out_path.resolve()))
            print('[OUT] Size (bytes):', out_path.stat().st_size)
    except Exception as e:
        print('[ERROR] Processing failed with exception:', e)


if __name__ == '__main__':
    main()