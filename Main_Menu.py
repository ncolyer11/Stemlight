import math
import tkinter as tk
import tkinter.font as font
from tkinter import messagebox

from Calculators.Trunk_Distribution_Calculator import MainWindow

from Assets import colours

from Calculators import (
    # Custom_Nylium_Grid_Heatmap_Calculator,
    # Nether_Tree_Farm_Layout_Efficiency_Calculator,
    # Nether_Tree_Farm_Rates_Calculator,
    # Nylium_Dispenser_Placement_Calculator,
    Trunk_Distribution_Calculator
)
# Define a dictionary to store instances of the window classes
window_instances = {}

def open_window(window_class):
    # If an instance of the window class already exists, focus on it
    
    if window_class in window_instances:
        print("we out here")
        window = window_instances[window_class]
        window.focus_force()
    else:
        print("we in here")
        root = tk.Toplevel()
        # Create a new instance of the window class
        window = window_class(root)
        window_instances[window_class] = window

# Define function to show help message
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
# icon_path = os.path.abspath('Assets\\ikon.ico')
# root.iconbitmap(icon_path)
root.configure(bg=colours.bg)
root.minsize(450, 200)

main_font = font.Font(family='Segoe UI Semibold', size=11)

# Define program buttons
programs = [
    # ("Farm Rates & Efficiency", Nether_Tree_Farm_Rates_Calculator.MainWindow),
    # ("Chart Viewer", Chart_Display.MainWindow),
    # ("Fungus Distribution", Nylium_Dispenser_Placement_Calculator.MainWindow),
    # ("Playerless Core Heatmap Gen", Custom_Nylium_Grid_Heatmap_Calculator.MainWindow),
    # ("VRM Decoder", Nether_Tree_Farm_Layout_Efficiency_Calculator.MainWindow),
    ("Trunk Distribution", Trunk_Distribution_Calculator.MainWindow),
    # ("Credits", Credits.MainWindow)
]

cols = 2
rows = math.ceil(len(programs) / cols)

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
i = 0
for label, window_class in programs:
    button = tk.Button(root, text=label, command=lambda w=window_class: open_window(w))
    button.config(activebackground=button.cget('bg'), bg=colours.bg, fg=colours.fg, font=main_font,
                  padx=5, pady=5, width=22, height=2)
    button.grid(row=i // cols, column=i % cols, padx=8, pady=5)
    i += 1

# Set equal weights to all rows in the grid
for i in range(len(programs) // 2):
    root.grid_rowconfigure(i, weight=1)

# Start main loop
root.mainloop()
