"""Shows credits"""

import ctypes
import tkinter as tk
from tkinter import ttk

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version
from src.Assets.helpers import resource_path, set_title_and_icon


def start(root):
    credits_text = (
        "Created: May 11, 2023\n"
        f"Version:{version}\n"
        "Made by: ncolyer"
    )

    # Create the main window
    child = tk.Toplevel(root)
    set_title_and_icon(child, "Credits")

    # Set the window size
    window_width = int(RSF*275)
    window_height = int(RSF*250)
    child.geometry(f"{window_width}x{window_height}")

    child.configure(bg=colours.bg)

    # Get the actual screen's width and height
    screen_width = child.winfo_screenwidth()
    screen_height = child.winfo_screenheight()
    try: 
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
    except:
        pass

    # Calculate the position to center the child window
    center_x = screen_width // 2 - child.winfo_reqwidth()
    center_y = screen_height // 2 - child.winfo_reqheight()
    
    # Position the child window in the center of the screen
    child.geometry(f"+{center_x}+{center_y}")
    
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
    except:
        pass
    child.mainloop()
