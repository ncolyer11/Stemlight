import os
import sys
import tkinter as tk
from tkinter import ttk

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def start(root):
    credits_text = (
        "Made by: ncolyer\n"
        "Created: 2023\n"
        f"Version:{version}"
    )

    # Create the main window
    child = tk.Toplevel(root)
    child.title(f"Stemlight{version}: Credits")

    # Set the window icon
    icon_path = resource_path('src/assets/icon.ico')
    child.iconbitmap(icon_path)

    # Set the window size
    window_width = int(RSF*275)
    window_height = int(RSF*250)
    child.geometry(f"{window_width}x{window_height}")

    child.configure(bg=colours.bg)
    # Get the root window's position and size
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    # Position the child window to the right of the root window
    child.geometry(f"+{root_x + root_width}+{root_y + root_height}")

    # Call update_idletasks to make sure widgets have been created
    child.update_idletasks()

    # Style for the text
    style = ttk.Style(child)
    style.configure("TLabel", font=("Segoe UI Semibold", int(RSF*14)), padding=(5, 5), background=colours.dark_orange)
    style.configure("Title.TLabel", font=("Segoe UI Semibold", int(RSF*20)), padding=(5, 5))

    # Create and place a title label
    title_label = ttk.Label(child, text="Stemlight", justify="center", style="Title.TLabel")
    title_label.grid(row=0, column=0, padx=10, pady=10)

    # Create and place a label for the credits text
    label = ttk.Label(child, text=credits_text, justify="center", style="TLabel", background=colours.menu_gradient[1])
    label.grid(row=1, column=0, padx=10, pady=int(RSF*30))

    # Center the content in the window
    child.columnconfigure(0, weight=1)
    child.rowconfigure(0, weight=1)

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    finally:
        child.mainloop()
