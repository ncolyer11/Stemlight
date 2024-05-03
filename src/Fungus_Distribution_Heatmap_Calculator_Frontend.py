"""Calculates distribution of fungus, and bone meal usage, \nfor a given grid of nylium, and placement and fire order of dispensers"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as font
import time
from PIL import Image, ImageDraw, ImageTk

from src.Dispenser_Placement_Optimiser import initialise_optimisation
from src.Fungus_Distribution_Backend import calculate_fungus_distribution
import src.Assets.colours as colours
from src.Assets.constants import RSF
from src.Assets.helpers import set_title_and_icon
from src.Assets.helpers import resource_path

WARPED = 0
CRIMSON = 1

# @TODO:
# label input for number of cycles
# hover over any cell to give you a tooltip of how many fungi and foliage are generated on top of
# it after N input cycles (usually just 1) and how much bm is used to grow in that spot, and if
# the cell is a dispenser,show how much bm it uses to produce fungi, 
# and if it's a cleared dispenser
# in each program, add a help menu item to the toolbar explaining how to use it
# Button to export nether tree growth heatmap from the fungi distribution data
# slider for selecting desired wart block/ bone meal efficiency
# an option for each dispenser to make it so it isn't affected by overlap (cleared by piston above)

# Non-linear scaling 
NLS = 1.765
WDTH = 92
HGHT = 46
PAD = 5
RAD = 26
DP = 5
MAX_SIDE_LEN = 10

class SlideSwitch(tk.Canvas):
    def __init__(self, parent, callback=None, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)

        self.configure(width=WDTH, height=HGHT)
        self.configure(highlightthickness=0)
        self.configure(bg=colours.bg)
        self.fungi_type = tk.StringVar(value="warped")

        # Create an image of a rounded rectangle
        self.rect_image = self.create_squircle(WDTH, HGHT, RAD, colours.warped)
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
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.warped)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, WDTH//4, HGHT//2)
            self.fungi_type.set("warped")
        else:
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.crimson)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, 3 * WDTH//4, HGHT//2)
            self.fungi_type.set("crimson")

        self.state = not self.state
        if self.callback:
            self.callback()
    
    def create_squircle(self, width, height, radius, fill):
        # Create a new image with transparent background
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        # Create a rounded rectangle on the image
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=fill, outline=colours.bg)

        return ImageTk.PhotoImage(image)

class App:
    def __init__(self, master):
        self.master = master
        self.grid = []
        self.dispensers = []
        self.nylium_type = tk.StringVar(value="warped")
        self.vars = []
        self.create_widgets()
        self.output_text_label = {}
        self.output_text_value = {}

    def create_widgets(self):
        self.master.configure(bg=colours.bg)
        style = ttk.Style()
    
        # Define the fonts
        large_button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*10))
        small_button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*7))
        checkbox_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*15))
        slider_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))

        output_title_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*13))
        label_font = font.Font(family='Segoe UI', size=int((RSF**NLS)*5))
    
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

        row_label = tk.Label(self.master, text="Length:", bg=colours.bg, fg=colours.fg, font=slider_font)
        row_label.pack()

        self.row_slider = tk.Scale(
            self.master, 
            from_=1, 
            to=MAX_SIDE_LEN, 
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.row_slider.set(5)
        self.row_slider.bind("<Double-Button-1>", self.reset_slider)
        self.row_slider.pack(pady=5)
        self.row_slider.pack()

        col_label = tk.Label(self.master, text="Width:", bg=colours.bg, fg=colours.fg, font=slider_font)
        col_label.pack()

        self.col_slider = tk.Scale(
            self.master, 
            from_=1, 
            to=MAX_SIDE_LEN, 
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )

        self.col_slider.set(5)
        self.col_slider.bind("<Double-Button-1>", self.reset_slider)
        self.col_slider.pack(pady=5)
        self.col_slider.pack()

        self.button_slider_frame = tk.Frame(self.master, bg=colours.bg)
        self.button_slider_frame.pack(pady=10)

        self.reset_button = tk.Button(self.button_slider_frame, text="Reset", command=self.reset_dispensers, font=small_button_font, bg=colours.warped)
        self.reset_button.pack(side=tk.RIGHT, padx=5)

        self.nylium_switch = SlideSwitch(self.button_slider_frame, callback=self.update_nylium_type)
        self.nylium_switch.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid_frame = tk.Frame(self.master, bg=colours.bg)
        self.grid_frame.pack(padx=10, pady=5)

        self.optimise_button = tk.Button(self.master, text="Optimise", command=self.optimise,
                                         font=large_button_font, bg=colours.crimson, pady=2)
        self.optimise_button.pack(pady=5)

        self.master_frame = tk.Frame(self.master)
        self.master_frame.pack()

        # Create a new frame for the output results
        self.output_frame = tk.Frame(self.master_frame, bg=colours.bg,
                                     highlightthickness=3, highlightbackground="grey")
        self.output_frame.grid(row=0, column=1, sticky='nsew')
        self.master_frame.grid_columnconfigure(1, weight=1)
        self.master_frame.grid_rowconfigure(0, weight=1)
    
        # Add a label to the output frame for output labels
        self.output_label = tk.Label(self.output_frame, text="Outputs", font=output_title_font,
                    bg=colours.bg, fg=colours.fg)
        self.output_label.grid(row=0, column=0, sticky='w')

        # Add a label to the output frame for output values
        self.output_value = tk.Label(self.output_frame, text="\t", font=output_title_font,
                    bg=colours.bg, fg=colours.fg)
        self.output_value.grid(row=0, column=1, sticky='w')

    def reset_slider(self, event):
        self.master.after(10, lambda: event.widget.set(5))
    
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
            for j, tile in enumerate(row):
                if self.vars[i][j].get() == 0:
                    tile[0].config(image=self.unchecked_image)
        self.calculate()

    def create_ordered_dispenser_array(self, rows, cols):
        # Sort the dispensers list by the time data
        sorted_dispensers = sorted(self.dispensers, key=lambda dispenser: dispenser[2])
        # Filter out only valid dispensers
        filtered_dispensers = [d for d in sorted_dispensers if d[0] < rows and d[1] < cols]

        # Create a 2D array with the same dimensions as self.vars, initialized with zeros
        dispenser_array = [[0 for _ in var_row] for var_row in self.vars]

        # Iterate over the sorted dispensers list
        for i, dispenser in enumerate(filtered_dispensers):
            # The order of the dispenser is i + 1
            # Set the corresponding element in the dispenser array to i + 1
            x, y = dispenser[:2]
            # Preserve initial time value 
            dispenser_array[x][y] = (i + 1, dispenser[2])

        return dispenser_array
    
    def update_grid(self, _):
        label_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*5))

        # Save the states of the checkboxes
        saved_states = [[var.get() for var in var_row] for var_row in self.vars]
        rows = self.row_slider.get()
        cols = self.col_slider.get()
        dispenser_array = self.create_ordered_dispenser_array(rows, cols)

        for row in self.grid:
            for cb, label in row:
                cb.destroy()
                if isinstance(label, tk.Label):
                    label.destroy()

        self.grid = []
        self.dispensers = []
        self.vars = []

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

                var_row.append(var)
                row.append((cb, None))
                # Restore the state of the checkbox, if it existed before
                if i < len(saved_states) and j < len(saved_states[i]):
                    var.set(saved_states[i][j])
                    if saved_states[i][j] == 1:
                        cb.config(image=self.checked_image)
                        label = tk.Label(self.grid_frame, text=str(dispenser_array[i][j][0]), font=label_font)
                        label.grid(row=i, column=j, padx=0, pady=0, sticky='se')
                        row[j] = (cb, label)
                        self.dispensers.append((i, j, dispenser_array[i][j][1]))
            self.grid.append(row)
            self.vars.append(var_row)

        self.calculate()

    def add_dispenser(self, x, y):
        label_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*5))

        # Toggle the state of the checkbox
        self.vars[x][y].set(not self.vars[x][y].get())

        # Update the image based on the state of the checkbox
        if self.vars[x][y].get() == 0:
            self.grid[x][y][0].config(image=self.unchecked_image)
            new_dispensers = []
            for d in self.dispensers:
                if d[:2] == (x, y):
                    continue
                new_dispensers.append(d)
                # Reorder dispensers after removing one in the middle
                label = tk.Label(self.grid_frame, text=len(new_dispensers), font=label_font)
                d_x = d[0]
                d_y = d[1]
                label.grid(row=d_x, column=d_y, padx=0, pady=0, sticky='se')  
                self.grid[d_x][d_y][1].destroy()
                # Update the grid with the label
                self.grid[d_x][d_y] = (self.grid[d_x][d_y][0], label) 
            

            self.dispensers = [d for d in self.dispensers if d[:2] != (x, y)]
            self.grid[x][y][1].destroy()
        else:
            self.grid[x][y][0].config(image=self.checked_image)
            self.dispensers.append((x, y, time.time()))
            label = tk.Label(self.grid_frame, text=str(len(self.dispensers)), font=label_font)
            # Place label in the bottom right corner
            label.grid(row=x, column=y, padx=0, pady=0, sticky='se')  
            # Update the grid with the label
            self.grid[x][y] = (self.grid[x][y][0], label)  
        self.calculate()

    def reset_dispensers(self):
        for i, row in enumerate(self.grid):
            for j, tile in enumerate(row):
                self.vars[i][j].set(0)
                tile[0].config(image=self.unchecked_image)
                if isinstance(tile[1], tk.Label):
                    tile[1].destroy()
        self.dispensers = []
        self.calculate()

    def optimise(self):
        fungi_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        dispenser_coordinates = [(d[0], d[1]) for d in self.dispensers]
        all_optimal_coords = initialise_optimisation(
            self.col_slider.get(), 
            self.row_slider.get(),
            len(dispenser_coordinates),
            fungi_type
        )
        if (all_optimal_coords == -1):
            messagebox.showinfo("Error", "Maximum runtime exceeded")
            return
        
        self.reset_dispensers()
        for disp_coord in all_optimal_coords[0]:
            self.add_dispenser(disp_coord[0], disp_coord[1])

    def calculate(self):
        self.dispensers.sort(key=lambda d: d[2])
        dispenser_coordinates = [(d[0], d[1]) for d in self.dispensers]
        fungi_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, *_ = \
            calculate_fungus_distribution(
                self.col_slider.get(), 
                self.row_slider.get(),
                len(dispenser_coordinates),
                dispenser_coordinates,
                fungi_type
            )
        
        output_labels = [
            f"Total {'Warped' if fungi_type == WARPED else 'Crimson'} Fungi",
            "Bone Meal to Produce a Fungus",
            "Bone Meal for Production",
            "Bone Meal for Growth",
            "Total Bone Meal Used",
            "Total Foliage"
        ]
        
        output_values = [
            round(total_fungi, DP),
            round(bm_for_prod / total_fungi, DP) if total_fungi != 0 else 0.0,
            round(bm_for_prod, DP),
            round(bm_for_grow, DP),
            round(bm_total, DP),
            round(total_plants, DP)
        ]
        label_font = font.Font(family='Segoe UI', size=int((RSF**NLS)*9))
        output_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))

        # Clear existing labels
        for label in self.output_text_label.values():
            label.destroy()
        self.output_text_label = {}

        for value_label in self.output_text_value.values():
            value_label.destroy()
        self.output_text_value = {}

        # Create the labels for outputs
        for i, label_text in enumerate(output_labels):
            # Create a label for the output
            label = tk.Label(self.output_frame, text=label_text, bg=colours.bg, fg=colours.fg, font=label_font)
            label.grid(row=i + 2, column=0, padx=PAD, pady=PAD, sticky="W")

            # Store the label in the dictionary for later use
            self.output_text_label[i] = label

        # Create the labels for output values
        for i, output_value in enumerate(output_values):
            # Create a label for the output value
            value_label = tk.Label(self.output_frame, text=output_value, bg=colours.bg, fg=colours.fg, font=output_font)
            value_label.grid(row=i + 2, column=1, padx=PAD, pady=PAD, sticky="WE")
            value_label.grid_columnconfigure(0, weight=1)  # Ensure the label fills the cell horizontally

            # Store the value label in the dictionary for later use
            self.output_text_value[i] = value_label

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
