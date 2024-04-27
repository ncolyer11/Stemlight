import os
import sys
import tkinter as tk

from Assets.version import version

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def set_title_and_icon(root, program_name):
    root.title(f"Stemlight{version}: {program_name}")
    try:
        # Try to use the .ico file
        icon_path = resource_path('src/Assets/icon.ico')
        root.iconbitmap(icon_path)
    except:
        # If that fails, try to use the .xbm file
        try:
            icon_path = resource_path('src/Assets/icon.xbm')
            root.iconbitmap('@' + icon_path)
        except:
            pass  # If that also fails, do nothing