import math
import os
import sys
import tkinter as tk
import tkinter.font as font
from tkinter import messagebox
import threading
import subprocess

from src import (
    Nether_Tree_Farm_Rates_Calculator,
    Chart_Display,
    Nylium_Dispenser_Placement_Calculator,
    Custom_Nylium_Grid_Heatmap_Calculator,
    Nether_Tree_Farm_Layout_Efficiency_Calculator,
    Trunk_Distribution_Calculator,
    Credits,
)

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

def run_python_code(python_file):
    python_file.start(root)

def show_help_message():
    messagebox.showinfo(
        "Help",
        "If you're experiencing a ModuleNotFoundError, try using VSCode and ensure that the following is in settings.json:\n\n"
        "\"terminal.integrated.env.windows\": {\n"
        "  \"PYTHONPATH\": \"${workspaceFolder}\"\n"
        "}",
        icon='question'
    )

def create_gradient(start_color, end_color, width, height, rows, cols):
    # Create a canvas and grid it into the root window
    canvas = tk.Canvas(root, width=width, height=height, borderwidth=0, highlightthickness=0)
    canvas.grid(row=0, column=0, rowspan=rows, columnspan=cols, sticky="nsew")

    # Configure grid weights to make the canvas fill the window
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Create a vertical gradient from start_color to end_color
    for y in range(height):
        r = int(int(start_color[1:3], 16) * (height - y) / height + int(end_color[1:3], 16) * y / height)
        g = int(int(start_color[3:5], 16) * (height - y) / height + int(end_color[3:5], 16) * y / height)
        b = int(int(start_color[5:], 16) * (height - y) / height + int(end_color[5:], 16) * y / height)
        color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        canvas.create_rectangle(0, y, width, y + 1, fill=color, outline="")

    # Bind the <Configure> event to the root window and add a function to handle it
    root.bind("<Configure>", lambda event: resize_canvas(event, canvas, start_color, end_color))

def resize_canvas(event, canvas, start_color, end_color):
    # Get the new size of the window
    width = event.width
    height = event.height

    # Update the size of the canvas
    canvas.config(width=width, height=height)
    # Delete the existing gradient
    canvas.delete("gradient")

    # Create a new gradient with the new size
    for y in range(height):
        r = int(int(start_color[1:3], 16) * (height - y) / height + int(end_color[1:3], 16) * y / height)
        g = int(int(start_color[3:5], 16) * (height - y) / height + int(end_color[3:5], 16) * y / height)
        b = int(int(start_color[5:], 16) * (height - y) / height + int(end_color[5:], 16) * y / height)
        color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        canvas.create_rectangle(0, y, width, y + 1, fill=color, outline="", tags="gradient")


# Create main window
root = tk.Tk()
root.title(f"Stemlight{version}: Main Menu")
icon_path = resource_path('src/assets/icon.ico')
root.iconbitmap(icon_path)
root.configure(bg=colours.bg)
root.minsize(int(RSF*450), int(RSF*200))

main_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*11))

# Program class to cleanly store program data
class Program:
    def __init__(self, id, program, label):
        self.id = id
        self.program = program
        self.label = label

programs = [
    Program(1, Nether_Tree_Farm_Rates_Calculator, "Farm Rates & Efficiency"),
    Program(2, Chart_Display, "Chart Viewer"),
    Program(3, Nylium_Dispenser_Placement_Calculator, "Fungus Distribution"),
    Program(4, Custom_Nylium_Grid_Heatmap_Calculator, "Playerless Core Heatmap Gen"),
    Program(5, Nether_Tree_Farm_Layout_Efficiency_Calculator, "VRM Decoder"),
    Program(6, Trunk_Distribution_Calculator, "Trunk Distribution"),
    Program(99, Credits, "Credits"),
]

cols = 2
rows = math.ceil(len(programs) / cols)

# Add background gradient
create_gradient(colours.menu_gradient[0], colours.menu_gradient[1], int(RSF*500), int(RSF*200), rows, cols)

# Create menu
toolbar = tk.Menu(root)
root.config(menu=toolbar)

file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# New Help menu
help_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
toolbar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="Module Not Found Error", command=show_help_message)

# Create buttons using a for loop
for i, program in enumerate(programs):
    button = tk.Button(
        root,
        text=program.label,
        command=lambda file=program.program: run_python_code(file),
        bg=colours.bg,
        fg=colours.fg,
        font=main_font,
        padx=5,
        pady=5,
        width=int((RSF**0.5)*22),
        height=int((RSF**0.7)*2)
    )
    button.config(activebackground=button.cget('bg'))
    button.grid(row=i // cols, column=i % cols, padx=8, pady=5)

# Set equal weights to all rows in the grid
for i in range(len(programs) // 2):
    root.grid_rowconfigure(i, weight=1)

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
finally:
    root.mainloop()
