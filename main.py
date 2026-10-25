"""
Banker's Algorithm Simulator — Main Entry Point
-----------------------------------------------
Launches the desktop GUI application.
Provides macOS-specific high-DPI scaling awareness and graceful error logging.

Usage:
    python3 main.py
"""

import sys
import os

# Silence macOS deprecated system Tkinter warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Ensure current directory is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import BankersSimulatorApp


def main():
    """Initializes and runs the Banker's Algorithm Desktop Simulator."""
    try:
        app = BankersSimulatorApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nBanker's Algorithm Simulator closed by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error launching Banker's Algorithm Simulator: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
