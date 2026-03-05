"""
main.py
-------
Entry point. Just launches the application window.

To run:
    python main.py
"""

import tkinter as tk
from ui import SLSSortingApp

if __name__ == "__main__":
    root = tk.Tk()
    SLSSortingApp(root)
    root.mainloop()
