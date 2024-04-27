"""Calculates distribution of fungus, and bone meal usage, \nfor a given grid of nylium, and placement and fire order of dispensers"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as font
import time
from PIL import Image, ImageDraw, ImageTk

from src.Fungus_Distribution_Backend import calculate_fungus_distribution
import src.Assets.colours as colours
from src.Assets.constants import RSF
from src.Assets.helpers import set_title_and_icon
from src.Assets.helpers import resource_path

# label input for number of cycles
# sidebar with a list of all dispensers and hover over a dispenser to tell u how much bm it uses per cycle
# reset button to clear all selections 

# Non-linear scaling factor
NLS = 1.765
WDTH = 92
HGHT = 46
PAD = 5
RAD = 26
DP = 5

def create_squircle(width, height, radius, fill):
    # Create a new image with transparent background
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    # Create a rounded rectangle on the image
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=fill, outline=colours.bg)

    return ImageTk.PhotoImage(image)

class SlideSwitch(tk.Canvas):
    def __init__(self, parent, callback=None, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)

        self.configure(width=WDTH, height=HGHT)
        self.configure(highlightthickness=0)
        self.configure(bg=colours.bg)
        self.fungi_type = tk.StringVar(value="warped")

        # Create an image of a rounded rectangle
        self.rect_image = create_squircle(WDTH, HGHT, RAD, colours.warped)
        self.rect = self.create_image(0, 0, image=self.rect_image, anchor='nw')
        self.new_image = self.rect_image

        # Create toggle circle
        circle_path = resource_path("src/Images/netherrack_circle.png")
        self.switch_image = tk.PhotoImage(file=circle_path)
        self.switch_image = self.switch_image.subsample(4, 4)
        self.oval = self.create_image(WDTH//4, HGHT//2, image=self.switch_image)

        self.bind("<Button-1>", self.toggle)

        self.state = False
        self.callback = callback

    def toggle(self, event):
        if self.state:
            self.new_image = create_squircle(WDTH, HGHT, RAD, colours.warped)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, WDTH//4, HGHT//2)
            self.fungi_type.set("warped")
        else:
            self.new_image = create_squircle(WDTH, HGHT, RAD, colours.crimson)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, 3 * WDTH//4, HGHT//2)
            self.fungi_type.set("crimson")

        self.state = not self.state
        if self.callback:
            self.callback()

class App:
    def __init__(self, master):
        self.master = master
        self.grid = []
        self.dispensers = []
        self.nylium_type = tk.StringVar(value="warped")
        self.vars = []
        self.create_widgets()

        # Create a new frame for the output results
        self.output_frame = tk.Frame(self.master, bg=colours.bg)
        self.output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        # Add a label to the output frame
        output_label = tk.Label(self.output_frame, text="Output",
                                font=("Segoe UI Semibold", int((RSF**NLS)*15)),
                                bg=colours.bg, fg=colours.fg)
        output_label.pack()
        # Add a text widget to this frame
        self.output_text = tk.Text(self.output_frame,
                                   bg=colours.bg, fg=colours.fg, height=12)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        label_font = ("Segoe UI Semibold", int((RSF**NLS)*9))
        output_font = ("Segoe UI", int((RSF**NLS)*9))

        self.output_text.tag_configure("label", font=label_font)
        self.output_text.tag_configure("output", font=output_font)

    def create_widgets(self):
        self.master.configure(bg=colours.bg)
        style = ttk.Style()
    
        # Define the font
        button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*11))
        checkbox_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*15))
        slider_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*15))
    
        style.configure(
            "TCheckbutton", 
            indicatorsize=120, 
            foreground=colours.bg, 
            background=colours.warped, 
            font=checkbox_font
        )
        style.configure("TScale", font=slider_font)

        # Create images for the checked and unchecked states
        checked_path = resource_path("src/Images/dispenser.png")
        unchecked_path = resource_path("src/Images/warped_nylium.png")
        self.checked_image = tk.PhotoImage(file=checked_path)
        self.unchecked_image = tk.PhotoImage(file=unchecked_path)

        # Resize the images
        self.checked_image = self.checked_image.subsample(4, 4)
        self.unchecked_image = self.unchecked_image.subsample(4, 4)
    
        self.row_slider = tk.Scale(
            self.master, 
            from_=1, 
            to=10, 
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.row_slider.set(5)
        self.row_slider.pack(pady=10)
        self.row_slider.pack()

        self.col_slider = tk.Scale(
            self.master, 
            from_=1, 
            to=10, 
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.col_slider.set(5)
        self.col_slider.pack(pady=1)
        self.col_slider.pack()

        self.nylium_switch = SlideSwitch(self.master, callback=self.update_nylium_type)
        self.nylium_switch.pack(pady=10)

        self.grid_frame = tk.Frame(self.master, bg=colours.bg, padx=10, pady=10)
        self.grid_frame.pack()
        self.calc_button = tk.Button(self.master, text="Calculate", command=self.calculate, font=button_font, bg=colours.crimson)
        self.calc_button.pack()

    def update_nylium_type(self):
        if self.nylium_type.get() == "warped":
            self.nylium_type.set("crimson")
            unchecked_path = resource_path("src/Images/crimson_nylium.png")
        else:
            self.nylium_type.set("warped")
            unchecked_path = resource_path("src/Images/warped_nylium.png")
        self.unchecked_image = tk.PhotoImage(file=unchecked_path)
        self.unchecked_image = self.unchecked_image.subsample(4, 4)
        # Update the images of the checkboxes
        for i, row in enumerate(self.grid):
            for j, cb in enumerate(row):
                if self.vars[i][j].get() == 0:
                    cb.config(image=self.unchecked_image)

    def update_grid(self, _):
        # Save the states of the checkboxes
        saved_states = [[var.get() for var in var_row] for var_row in self.vars]
    
        for row in self.grid:
            for cb in row:
                cb.destroy()
        self.grid = []
        self.dispensers = []
        self.vars = []
        rows = self.row_slider.get()
        cols = self.col_slider.get()
        for i in range(rows):
            row = []
            var_row = []
            for j in range(cols):
                var = tk.IntVar()
                cb = tk.Button(
                    self.grid_frame,
                    image=self.unchecked_image,
                    borderwidth=0,
                    highlightthickness=0,
                    bd=1,
                    bg=colours.phtalo_green,
                    command=lambda x=i, y=j: self.add_dispenser(x, y)
                )
                cb.grid(row=i, column=j, padx=0, pady=0)
                row.append(cb)
                var_row.append(var)
                # Restore the state of the checkbox, if it existed before
                if i < len(saved_states) and j < len(saved_states[i]):
                    var.set(saved_states[i][j])
                    if saved_states[i][j] == 1:
                        cb.config(image=self.checked_image)
                        self.dispensers.append((i, j, time.time()))
            self.grid.append(row)
            self.vars.append(var_row)

    def add_dispenser(self, x, y):
        # Toggle the state of the checkbox
        self.vars[x][y].set(not self.vars[x][y].get())

        # Update the image based on the state of the checkbox
        if self.vars[x][y].get() == 0:
            self.grid[x][y].config(image=self.unchecked_image)
            self.dispensers = [d for d in self.dispensers if d[:2] != (x, y)]
        else:
            self.grid[x][y].config(image=self.checked_image)
            self.dispensers.append((x, y, time.time()))

    def calculate(self):
        self.dispensers.sort(key=lambda d: d[2])
        dispenser_coordinates = [(d[0], d[1]) for d in self.dispensers]
        fungi_type = 1 if self.nylium_type.get() == "crimson" else 0
        total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, fungi_type = \
            calculate_fungus_distribution(
                self.col_slider.get(), 
                self.row_slider.get(),
                len(dispenser_coordinates),
                dispenser_coordinates,
                fungi_type
            )
        
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, "Fungi Type: ", "label")
        self.output_text.insert(tk.END, f"{'Warped' if fungi_type == 0 else 'Crimson'}\n", "output")
        self.output_text.insert(tk.END, "Total Fungi: ", "label")
        self.output_text.insert(tk.END, f"{round(total_fungi, DP)}\n", "output")
        self.output_text.insert(tk.END, "Total BM: ", "label")
        self.output_text.insert(tk.END, f"{round(bm_total, DP)}\n", "output")
        self.output_text.insert(tk.END, "BM for Production: ", "label")
        self.output_text.insert(tk.END, f"{round(bm_for_prod, DP)}\n", "output")
        self.output_text.insert(tk.END, "BM for Growth: ", "label")
        self.output_text.insert(tk.END, f"{round(bm_for_grow, DP)}\n", "output")
        self.output_text.insert(tk.END, "Total Foliage: ", "label")
        self.output_text.insert(tk.END, f"{round(total_plants, DP)}\n", "output")

def start(root):
    child = tk.Toplevel(root)
    set_title_and_icon(child, "Playerless Core Tools")

    child.configure(bg=colours.bg)
    child.size = (int(RSF*300), int(RSF*325))

    # Create menu
    toolbar = tk.Menu(child)
    child.config(menu=toolbar)

    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.destroy)

    # Get the root window's position and size
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()

    # Position the child window to the top right of the root window
    child.geometry(f"+{root_x + root_width}+{root_y}")

    # Update the window so it actually appears in the correct position
    child.update_idletasks()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = App(child)
    child.mainloop()
