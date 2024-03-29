import math
import os
import tkinter as tk
import tkinter.font as font
from tkinter import messagebox
import threading
import subprocess

from Assets import colours

# Define function to open a Python file
def open_file(folder, subfolder, program_name):
    file_path = f"./{folder}/{subfolder}/{program_name}"
    subprocess.call(["python", file_path])

def open_file_single_instance(folder, subfolder, file):
    thread = threading.Thread(target=open_file, args=(folder, subfolder, file))
    thread.start()

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
root.title("Stemlight: Main Menu")
icon_path = os.path.abspath('Assets\\ikon.ico')
root.iconbitmap(icon_path)
root.configure(bg=colours.bg)
root.minsize(450, 200)

main_font = font.Font(family='Segoe UI Semibold', size=11)

# Define file paths, names, and button labels
programs = [
    {
        "id": 1,
        "file": "Nether_Tree_Farm_Rates_Calculator.py",
        "folder": "Calculators",
        "subfolder": "Nether_Tree_Farm_Rates_Calculator",
        "label": "Farm Rates & Efficiency"
    },
    {
        "id": 2,
        "file": "Chart_Display.py",
        "folder": "Charts",
        "subfolder": "Chart_Display",
        "label": "Chart Viewer"
    },
    {
        "id": 3,
        "file": "Nylium_Dispenser_Placement_Calculator.py",
        "folder": "Calculators",
        "subfolder": "Nylium_Dispenser_Placement_Calculator",
        "label": "Fungus Distribution"
    },
    {
        "id": 4,
        "file": "Custom_Nylium_Grid_Heatmap_Calculator.py",
        "folder": "Calculators",
        "subfolder": "Custom Nylium Grid Heatmap Calculator",
        "label": "Playerless Core Heatmap Gen"
    },
    {
        "id": 5,
        "file": "Nether_Tree_Farm_Layout_Efficiency_Calculator.py",
        "folder": "Calculators",
        "subfolder": "Nether_Tree_Farm_Layout_Efficiency_Calculator",
        "label": "VRM Decoder"
    },
    {
        "id": 6,
        "file": "Trunk_Distribution_Calculator.py",
        "folder": "Calculators",
        "subfolder": "Trunk_Distribution_Calculator",
        "label": "Trunk Distribution"
    },
    {
        "id": 99,
        "file": "Credits.py",
        "folder": "Assets",
        "subfolder": "Credits",
        "label": "Credits"
    },
]

# Sort programs based on 'id'
programs.sort(key=lambda x: x["id"])

folder_names = [program["folder"] for program in programs]
subfolder_names = [program["subfolder"] for program in programs]
file_names = [program["file"] for program in programs]
button_labels = [program["label"] for program in programs]

cols = 2
rows = math.ceil(len(file_names) / cols)

# Add background gradient
create_gradient(colours.menu_gradient[0], colours.menu_gradient[1], 500, 200, rows, cols)

# Create menu
toolbar = tk.Menu(root)
root.config(menu=toolbar)

file_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# New Help menu
help_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="Module Not Found Error", command=show_help_message)

# Create buttons using a for loop
for i in range(len(file_names)):
    button = tk.Button(root, text=button_labels[i],
                       command=lambda folder=folder_names[i], subfolder=subfolder_names[i],
                                      file=file_names[i]: open_file_single_instance(folder, subfolder, file))
    button.config(activebackground=button.cget('bg'), bg=colours.bg, fg=colours.fg, font=main_font,
                  padx=5, pady=5, width=22, height=2)
    button.grid(row=i // cols, column=i % cols, padx=8, pady=5)

# Set equal weights to all rows in the grid
for i in range(len(file_names) // 2):
    root.grid_rowconfigure(i, weight=1)

# Start main loop
root.mainloop()
