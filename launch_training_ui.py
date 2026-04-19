"""
Launcher script for Training UI
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from training_ui import main

if __name__ == "__main__":
    main()