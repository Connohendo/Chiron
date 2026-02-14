"""Chiron – Job Application Tracker

Launch the desktop application:
    python src/main.py
"""

import sys
import os

# Ensure the project root is importable so `from src.…` works everywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import ChironApp  # noqa: E402


def main():
    app = ChironApp()
    app.mainloop()


if __name__ == "__main__":
    main()
