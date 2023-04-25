import tkinter as tk
import tkinter.font as font
import threading
import os

from Assets import colours


# Define function to open a Python file
def open_file(folder, file_name):
    os.system(f"python ../{folder}/{file_name}")


def open_file_single_instance(folder, file):
    thread = threading.Thread(target=open_file, args=(folder, file))
    thread.start()


# Create main window
root = tk.Tk()
root.title("Stemlight: Main Menu")
root.iconbitmap('../../Assets/ikon.ico')
root.configure(bg=colours.bg)

main_font = font.Font(family='Segoe UI Semibold', size=11)


def create_gradient(start_color, end_color, width, height):
    # Create a canvas and grid it into the root window
    canvas = tk.Canvas(root, width=width, height=height, borderwidth=0, highlightthickness=0)
    canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")

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


create_gradient(colours.menu_gradient[0], colours.menu_gradient[1], 500, 200)

# Create menu
toolbar = tk.Menu(root)
root.config(menu=toolbar)

file_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# Define file names and button labels
file_names = [
    "Nether_Tree_Farm_Layout_Efficiency_Calculator.py",
    "Nether_Tree_Farm_Rates_Calculator.py",
    "Nylium_Dispenser_Placement_Calculator.py",
    "Trunk_Distribution_Calculator.py"
]

folder_names = [
    "Nether_Tree_Farm_Layout_Efficiency_Calculator",
    "Nether_Tree_Farm_Rates_Calculator",
    "Nylium_Dispenser_Placement_Calculator",
    "Trunk_Distribution_Calculator"
]

button_labels = [
    "Layout Efficiency",
    "Farm Rates",
    "Fungus Distribution",
    "Trunk Distribution"
]

# Create buttons using a for loop
for i in range(len(file_names)):
    button = tk.Button(root, text=button_labels[i],
                       command=lambda file=file_names[i], folder=folder_names[i]: open_file_single_instance(folder,
                                                                                                            file))
    button.config(activebackground=button.cget('bg'), bg=colours.bg, fg=colours.fg, font=main_font,
                  padx=5, pady=5, width=22, height=2)
    button.grid(row=i // 2, column=i % 2, padx=8, pady=5)

# Set equal weights to all rows in the grid
for i in range(len(file_names) // 2):
    root.grid_rowconfigure(i, weight=1)

# Start main loop
root.mainloop()
