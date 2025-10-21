#!/usr/bin/env python3
"""
Quick Cut - Video Silence Remover
A minimal video editor that automatically removes silent sections from videos.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main application entry point."""
    import tkinter as tk
    from gui.main_window import MainWindow
    
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()