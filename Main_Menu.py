import math
import tkinter as tk
import tkinter.font as font
from tkinter import messagebox

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.helpers import ToolTip, set_title_and_icon

from src import (
    Nether_Tree_Farm_Rates_Calculator,
    Chart_Display,
    Nether_Tree_Farm_Layout_Efficiency_Calculator,
    Playerless_Core_Tools_Frontend,
    Trunk_Distribution_Calculator,
    Credits,
)

# TODO:
# Convert *all* programs to use classes for their program structure and also ahh do more
# refactoring using dataclasses like you done already with the playerless core tools frontend
# add linting and some other github workflow or whatever

# Program class to cleanly store program data
class Program:
    """A class to store program data."""
    def __init__(self, id, program, label):
        self.id = id
        self.program = program
        self.label = label
        self.description = program.__doc__

def main():
    # Create main window
    root = tk.Tk()
    set_title_and_icon(root, "Main Menu")

    root.configure(bg=colours.bg)
    root.minsize(int(RSF*450), int(RSF*200))
    # Place the menu just offset from the top left corner
    root.geometry(f"+50+50")
    root.update_idletasks()

    main_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*11))

    programs = [
        Program(1, Nether_Tree_Farm_Rates_Calculator, "Farm Rates & Efficiency"),
        Program(2, Chart_Display, "Chart Viewer"),
        Program(3, Playerless_Core_Tools_Frontend, "Playerless Core Tools"),
        Program(4, Nether_Tree_Farm_Layout_Efficiency_Calculator, "VRM Decoder"),
        Program(5, Trunk_Distribution_Calculator, "Trunk Distribution"),
        Program(99, Credits, "Credits"),
    ]

    cols = 2
    rows = math.ceil(len(programs) / cols)

    # Add background gradient
    create_gradient(root, colours.menu_gradient[0], colours.menu_gradient[1], int(RSF*500), int(RSF*200), rows, cols)

    # Create menu
    toolbar = tk.Menu(root)
    root.config(menu=toolbar)

    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=root.destroy)

    # New Help menu
    help_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Module Not Found Error", command=show_help_message)

    # Create buttons using a for loop
    for i, program in enumerate(programs):
        button = tk.Button(
            root,
            text=program.label,
            command=lambda file=program.program: run_python_code(root, file),
            bg=colours.bg,
            fg=colours.fg,
            font=main_font,
            padx=5,
            pady=5,
            width=int((RSF**0.5)*22),
            height=int((RSF**0.7)*2),
            # state="disabled" # cool good to know
        )
        button.config(activebackground=button.cget("bg"))

        # Create a tooltip for the button
        tooltip = ToolTip(button, program.description)


        # If it's the last button and it's the only one in its row, span it across all columns
        if i == len(programs) - 1 and len(programs) % cols == 1:
            button.grid(row=i // cols, column=0, columnspan=cols, padx=8, pady=5)
        else:
            button.grid(row=i // cols, column=i % cols, padx=8, pady=5)

    # Set equal weights to all rows in the grid
    for j in range(cols):
        root.grid_columnconfigure(j, weight=1)
    for i in range((len(programs) + cols - 1) // cols):
        root.grid_rowconfigure(i, weight=1)

    root.mainloop()

#########################
### HELPERS & DISPLAY ###
#########################
def run_python_code(root, python_file):
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

def create_gradient(root, start_color, end_color, width, height, rows, cols):
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

if __name__ == "__main__":
    main()