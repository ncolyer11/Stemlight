import math
import tkinter as tk
from tkinter import ttk
import tkinter.font as font
from tkinter import messagebox

from src import (
    Nether_Tree_Farm_Rates_Calculator,
    Chart_Display,
    Nether_Tree_Farm_Layout_Efficiency_Calculator,
    Playerless_Core_Tools_Frontend,
    Trunk_Distribution_Calculator,
    Credits,
)

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version
from src.Assets.helpers import resource_path, set_title_and_icon

# Program class to cleanly store program data
class Program:
    """A class to store program data."""
    def __init__(self, id, program, label):
        self.id = id
        self.program = program
        self.label = label
        self.description = program.__doc__

# ToolTip class to display tooltips
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, tip_text, x, y):
        "Display text in a tooltip window"
        if self.tip_window or not tip_text:
            return
        # x += self.widget.winfo_width() // 2
        # y += self.widget.winfo_height() // 2
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        main_font = font.Font(family='Segoe UI', size=int((RSF**1.765)*8))

        # @TODO update formatting for tooltips
        label = tk.Label(tw, text=tip_text, justify=tk.LEFT,
                    background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                    font=main_font)
        label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


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

def main():
    # Create main window
    root = tk.Tk()
    set_title_and_icon(root, "Main Menu")

    root.configure(bg=colours.bg)
    root.minsize(int(RSF*450), int(RSF*200))

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
            height=int((RSF**0.7)*2)
        )
        button.config(activebackground=button.cget('bg'))

        # Create a tooltip for the button
        tooltip = ToolTip(button)
        button.bind("<Enter>", lambda event, 
                    prog=program: tooltip.show_tip(prog.description, 
                                                event.x_root, event.y_root))
        button.bind("<Leave>", lambda event: tooltip.hide_tip())


        # If it's the last button and it's the only one in its row, span it across all columns
        if i == len(programs) - 1 and len(programs) % cols == 1:
            button.grid(row=i // cols, column=0, columnspan=cols, padx=8, pady=5)
        else:
            button.grid(row=i // cols, column=i % cols, padx=8, pady=5)

    # Set equal weights to all rows in the grid
    for i in range(len(programs) // 2):
        root.grid_rowconfigure(i, weight=1)

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    root.mainloop()

if __name__ == "__main__":
    main()