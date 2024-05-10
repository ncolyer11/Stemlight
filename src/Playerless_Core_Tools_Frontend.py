"""Calculates distribution of fungus, and bone meal usage, \nfor a given grid of nylium, and placement and fire order of dispensers"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as font
import time
from PIL import Image, ImageDraw, ImageTk
import numpy as np

from Main_Menu import ToolTip
from src.Stochastic_Optimisation import start_optimisation
from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.helpers import set_title_and_icon
from src.Assets.helpers import resource_path
from src.Custom_Nylium_Grid_Heatmap_Calculator import export_custom_heatmaps
from src.Fungus_Distribution_Backend import calculate_fungus_distribution

# @TODO:
# right click any cell to show how many fungi and foliage are generated on top of
# it after N input cycles (usually just 1) and how much bm is used to grow in that spot, and if the
# cell is a dispenser, show how much bm it uses to produce fungi, and if it's a cleared dispenser (this can actually be shown by replacing the dispenser png with a half piston half dispenser png)
# by 2 columns to fit individual block info that appears for any block you right click on

# an option for each dispenser to make it so it isn't affected by overlap (cleared by piston above)
# ^ middle click dispenser

# in each program, add a help menu item to the toolbar explaining how to use it

# Non-linear scaling 
NLS = 1.765
WDTH = 92
HGHT = 46
PAD = 5
RAD = 26
DP = 5
MAX_SIDE_LEN = 9
WARPED = 0
CRIMSON = 1

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
        draw.rounded_rectangle([(0, 0), (width, height)], 
                               radius=radius, fill=fill, outline=colours.bg)

        return ImageTk.PhotoImage(image)

class App:
    def __init__(self, master):
        self.master = master
        self.grid = []
        self.dispensers = []
        self.nylium_type = tk.StringVar(value="warped")
        self.run_time = 7
        self.vars = []
        self.create_widgets()
        self.output_text_label = {}
        self.output_text_value = {}
        self.info_text_label = {}
        self.info_text_value = {}
        self.selected_block = ()

        clearing_path = resource_path("src/Images/cleared_dispenser.png")
        self.clearing_image = tk.PhotoImage(file=clearing_path)
        self.clearing_image = self.clearing_image.subsample(3, 3)

        # Create menu
        toolbar = tk.Menu(master)
        master.config(menu=toolbar)

        file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=master.destroy)

        help_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="What's this Tool for?", command=self.show_info_message)

        run_time_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="Run Time", menu=run_time_menu)

        time_init = tk.StringVar(value="7")
        for time in [1, 4, 7, 10, 15, 30, 60]:
            run_time_menu.add_radiobutton(label=time, variable=time_init, value=time,
                                        command=lambda time=time: self.set_rt(time))

    def show_info_message(self):
        """Provide some information to the user about what this tool is used for"""
        messagebox.showinfo(
            "Information",
            "This tool is used to optimise the placement of dispensers on a platform of nylium "
            "such that their position and ordering maximises fungus production, whilst not exceeding "
            "a given bone meal efficiency requirement.",
            icon='question'
        )

    def create_widgets(self):
        self.master.configure(bg=colours.bg)
        style = ttk.Style()
    
        # Define the fonts
        large_button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*10))
        small_button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*7))
        checkbox_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*15))
        slider_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))

        output_title_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*13))
        output_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))
    
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
        self.checked_image = self.checked_image.subsample(3, 3)
        self.unchecked_image = self.unchecked_image.subsample(3, 3)

        self.create_sliders()

        self.button_slider_frame = tk.Frame(self.master, bg=colours.bg)
        self.button_slider_frame.pack(pady=10)  

        self.reset_button = tk.Button(self.button_slider_frame, text="Reset", command=self.reset_dispensers, font=small_button_font, bg=colours.warped)
        self.reset_button.pack(side=tk.RIGHT, padx=5)

        self.nylium_switch = SlideSwitch(self.button_slider_frame, callback=self.update_nylium_type)
        self.nylium_switch.pack(side=tk.LEFT, padx=5, pady=5)



        self.grid_frame = tk.Frame(self.master, bg=colours.bg)
        self.grid_frame.pack(pady=5)

        self.optimise_button = tk.Button(self.master, text="Optimise", command=self.optimise,
                                         font=large_button_font, bg=colours.crimson, pady=2)
        self.optimise_button.pack(pady=5)

        self.export_button = tk.Button(self.master, text="Export", command=self.export_heatmaps,
                                         font=large_button_font, bg=colours.aqua_green,
                                         pady=2, padx=16)
        self.export_button.pack(pady=5)

        self.master_frame = tk.Frame(self.master)
        self.master_frame.pack(pady=5)

        # Create a new frame for the output results
        self.output_frame = tk.Frame(self.master_frame, bg=colours.bg,
                                     highlightthickness=3, highlightbackground="grey")
        self.output_frame.grid(row=0, column=1, sticky='nsew')
    
        # Add a label to the output frame for output labels
        self.output_label = tk.Label(self.output_frame, text="Outputs", font=output_title_font,
                    bg=colours.bg, fg=colours.fg)
        self.output_label.grid(row=0, column=0, sticky='w')

        # Add a label to the output frame for output values
        self.output_value = tk.Label(self.output_frame, text="\t", font=output_title_font,
                    bg=colours.bg, fg=colours.fg)
        self.output_value.grid(row=0, column=1, sticky='w')

        # Add a label to display the stats of a selected individual block
        self.block_info_title = tk.Label(self.output_frame, text="Block Stats\t", font=output_title_font,
                    bg=colours.bg, fg=colours.fg)
        self.block_info_title.grid(row=0, column=2, sticky='w')

        # Add a label to the output frame for output values
        self.info_value = tk.Label(self.output_frame, text="\t", font=output_title_font,
                    bg=colours.bg, fg=colours.fg)
        self.info_value.grid(row=0, column=3, sticky='w')

    def create_sliders(self):
        self.master_frame = tk.Frame(self.master)
        self.master_frame.pack(pady=5)

        # Create a new frame for the output results
        self.slider_frame = tk.Frame(self.master_frame, bg=colours.bg)
        self.slider_frame.grid(row=0, column=0, sticky='nsew')

        slider_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))
        row_label = tk.Label(self.slider_frame, text="Length:", bg=colours.bg, fg=colours.fg, font=slider_font)
        row_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.row_slider = tk.Scale(
            self.slider_frame, 
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
        self.row_slider.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        col_label = tk.Label(self.slider_frame, text="Width:", bg=colours.bg, fg=colours.fg, font=slider_font)
        col_label.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.col_slider = tk.Scale(
            self.slider_frame, 
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
        self.col_slider.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.cycles_label = tk.Label(self.slider_frame, text="No. Cycles:", bg=colours.bg, fg=colours.fg, font=slider_font)
        self.cycles_label.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        cycles_tooltip = ToolTip(self.cycles_label)
        self.cycles_label.bind("<Enter>", lambda event: 
                    cycles_tooltip.show_tip((
                        "Set how many times the dispensers are activated."),
                        event.x_root, event.y_root))
        self.cycles_label.bind("<Leave>", lambda event: cycles_tooltip.hide_tip())
        self.cycles_slider = tk.Scale(
            self.slider_frame, 
            from_=1, 
            to=7,
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.cycles_slider.set(1)
        self.cycles_slider.bind("<Double-Button-1>", lambda event: self.reset_slider(event, 1))
        self.cycles_slider.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

        self.wb_effic_label = tk.Label(self.slider_frame, text="Wart Blocks/Fungus:", 
                                       bg=colours.bg, fg=colours.fg, font=slider_font)
        self.wb_effic_label.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        wb_effic_tooltip = ToolTip(self.wb_effic_label)
        self.wb_effic_label.bind("<Enter>", lambda event: 
                    wb_effic_tooltip.show_tip((
                        "Restrict optimal solutions to require a certain bone meal\n"
                        "(or ~8 composted wart blocks) per fungus produced efficiency."),
                        event.x_root, event.y_root))
        self.wb_effic_label.bind("<Leave>", lambda event: wb_effic_tooltip.hide_tip())
        self.wb_effic_slider = tk.Scale(
            self.slider_frame, 
            from_=20, 
            to=60, 
            orient=tk.HORIZONTAL, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250,
            resolution=0.1
        )
        self.wb_effic_slider.set(60)
        self.wb_effic_slider.bind("<Double-Button-1>", lambda event: self.reset_slider(event, 60))
        self.wb_effic_slider.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")      

    def reset_slider(self, event, default=5):
        self.master.after(10, lambda: event.widget.set(default))
    
    def update_nylium_type(self):
        if self.nylium_type.get() == "warped":
            self.nylium_type.set("crimson")
            unchecked_path = resource_path("src/Images/crimson_nylium.png")
        else:
            self.nylium_type.set("warped")
            unchecked_path = resource_path("src/Images/warped_nylium.png")
        self.unchecked_image = tk.PhotoImage(file=unchecked_path)
        self.unchecked_image = self.unchecked_image.subsample(3, 3)
        # Update the images of the checkboxes
        for i, row in enumerate(self.grid):
            for j, tile in enumerate(row):
                if self.vars[i][j].get() == 0:
                    tile[0].config(image=self.unchecked_image)
        self.calculate()
        self.display_block_info()

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
                # Right-click to view individual block info
                cb.bind("<Button-3>", lambda event, x=i, y=j: self.display_block_info(x, y))
                # Middle-click to set to a clearing dispenser
                cb.bind("<Button-2>", lambda event, x=i, y=j: self.set_clearing_dispenser(x, y))

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
        self.display_block_info()

    def add_dispenser(self, x, y, cleared=False):
        label_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*5))
        border_path = resource_path("src/Images/selected_block.png")
        self.border_image = tk.PhotoImage(file=border_path)
        self.border_image = self.border_image.subsample(3, 3)

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
            if cleared == True:
                self.grid[x][y][0].config(image=self.clearing_image)
                self.dispensers.append((x, y, time.time(), 1))
            else:
                self.grid[x][y][0].config(image=self.checked_image)
                self.dispensers.append((x, y, time.time(), 0))
            label = tk.Label(self.grid_frame, text=str(len(self.dispensers)), font=label_font)
            # Place label in the bottom right corner
            label.grid(row=x, column=y, padx=0, pady=0, sticky='se')  
            # Update the grid with the label
            self.grid[x][y] = (self.grid[x][y][0], label)  
        self.calculate()
        self.display_block_info()

    def reset_dispensers(self):
        for i, row in enumerate(self.grid):
            for j, tile in enumerate(row):
                self.vars[i][j].set(0)
                tile[0].config(image=self.unchecked_image)
                if isinstance(tile[1], tk.Label):
                    tile[1].destroy()
        self.dispensers = []
        self.calculate()
        self.display_block_info()

    def optimise(self):
        fungi_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        disp_coords = [(d[0], d[1]) for d in self.dispensers]
        cleared_array = [d[3] for d in self.dispensers]
        if len(disp_coords) == 0:
            return

        optimal_coords = start_optimisation(
            len(disp_coords),
            self.col_slider.get(), 
            self.row_slider.get(),
            self.wb_effic_slider.get(),
            fungi_type,
            self.run_time
        )

        if optimal_coords == -1:
            messagebox.showwarning("Error", "Maximum runtime exceeded.")
            return
        elif ([-1, -1] in optimal_coords or len(optimal_coords) == 0):
            messagebox.showinfo(
                "Optimisation Notice",
                "No optimal solution found for\n"
                "given wart block efficiency."
            )
            return
        self.reset_dispensers()
        for i, disp_coord in enumerate(optimal_coords):
            self.add_dispenser(disp_coord[0], disp_coord[1], cleared_array[i])
            
    def export_heatmaps(self):
        self.dispensers.sort(key=lambda d: d[2])
        dispenser_coordinates = [(d[0], d[1]) for d in self.dispensers]
        fungi_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED        
        disp_foliage_grids = \
            calculate_fungus_distribution(
                self.col_slider.get(), 
                self.row_slider.get(),
                len(dispenser_coordinates),
                dispenser_coordinates,
                fungi_type,
                self.cycles_slider.get()
            )[5]
        result = export_custom_heatmaps(
            self.col_slider.get(),
            self.row_slider.get(),
            np.sum(disp_foliage_grids, axis=0)
        )
        if result == 0:
            messagebox.showinfo("Success", "Heatmaps exported to weighted_fungi_heatmap.xlsx")
        else:
            messagebox.showwarning("Export Error", f"An error occurred:\n{result}")    

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
                fungi_type,
                self.cycles_slider.get()
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
        
        bm_for_prod_tooltip = ToolTip(self.output_text_label[2])
        self.output_text_label[2].bind("<Enter>", lambda event: 
                    bm_for_prod_tooltip.show_tip((
                        "Bone meal spent by the nylium dispensers that creates the fungi.\n"
                        "Factors in bone meal retrieved from composting excess foliage."),
                        event.x_root, event.y_root))
        self.output_text_label[2].bind("<Leave>", lambda event: bm_for_prod_tooltip.hide_tip())
        
        bm_for_growth_tooltip = ToolTip(self.output_text_label[2])
        self.output_text_label[3].bind("<Enter>", lambda event: 
                    bm_for_growth_tooltip.show_tip((
                        "Bone meal spent on growing already produced fungi."),
                        event.x_root, event.y_root))
        self.output_text_label[3].bind("<Leave>", lambda event: bm_for_growth_tooltip.hide_tip())
        
        # Create the labels for output values
        for i, output_value in enumerate(output_values):
            # Create a label for the output value
            value_label = tk.Label(self.output_frame, text=output_value, bg=colours.bg, fg=colours.fg, font=output_font)
            value_label.grid(row=i + 2, column=1, padx=PAD, pady=PAD, sticky="WE")
            value_label.grid_columnconfigure(0, weight=1)  # Ensure the label fills the cell horizontally

            # Store the value label in the dictionary for later use
            self.output_text_value[i] = value_label
    
    def display_block_info(self, x=None, y=None):
        # Return if no block is selected
        if not self.selected_block and x == None:
            return
        # Reset labels and deselect block if already selected
        elif (x, y) == self.selected_block:
            self.selected_block = ()
            for label in self.info_text_label.values():
                label.destroy()
            self.info_text_label = {}

            for value_label in self.info_text_value.values():
                value_label.destroy()
            self.info_text_value = {}
            return
        # Calling with empty arguments simply updates the currently selected block
        elif x is None and y is None:
            x, y = self.selected_block
        # Default behaviour is to just select a new block
        else:
            self.selected_block = (x, y)
    
        self.dispensers.sort(key=lambda d: d[2])
        dispenser_coordinates = [(d[0], d[1]) for d in self.dispensers]
        fungi_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        *_, disp_foliage_grids, disp_des_fungi_grids = \
            calculate_fungus_distribution(
                self.col_slider.get(), 
                self.row_slider.get(),
                len(dispenser_coordinates),
                dispenser_coordinates,
                fungi_type,
                self.cycles_slider.get()
            )
        
        info_labels = [
            f"{'Warped' if fungi_type == WARPED else 'Crimson'} Fungi",
        ]
        info_values = [
            round(np.sum(disp_des_fungi_grids, axis=0)[x, y], DP)
        ]
        # If selected block is a dispenser, include additional info
        if (x,y) in dispenser_coordinates:
            index = dispenser_coordinates.index((x, y))
            disp_chance = np.sum(disp_foliage_grids[:index], axis=0)[x,y]
            info_labels.append("Bone meal used")
            info_labels.append("Position")
            info_labels.append(f"{'Warped' if fungi_type == WARPED else 'Crimson'} Fungi Produced")
            info_values.append(round(1 - disp_chance, DP))
            info_values.append(index + 1)
            info_values.append(round(np.sum(disp_des_fungi_grids[index]), DP))
        
        label_font = font.Font(family='Segoe UI', size=int((RSF**NLS)*9))
        output_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))

        # Clear existing labels
        for label in self.info_text_label.values():
            label.destroy()
        self.info_text_label = {}

        for value_label in self.info_text_value.values():
            value_label.destroy()
        self.info_text_value = {}

        # Create the labels for info labels
        for i, label_text in enumerate(info_labels):
            label = tk.Label(self.output_frame, text=label_text, bg=colours.bg, fg=colours.fg, font=label_font)
            label.grid(row=i + 2, column=2, padx=PAD, pady=PAD, sticky="W")

            # Store the label in the dictionary for later use
            self.info_text_label[i] = label

        # Create the labels for block info values
        for i, output_value in enumerate(info_values):
            label = tk.Label(self.output_frame, text=output_value, bg=colours.bg, fg=colours.fg, font=output_font)
            label.grid(row=i + 2, column=3, padx=PAD, pady=PAD, sticky="WE")
            label.grid_columnconfigure(0, weight=1)  # Ensure the label fills the cell horizontally

            # Store the value label in the dictionary for later use
            self.info_text_value[i] = label
    
    def set_clearing_dispenser(self, x, y):
        """Set a dispenser to a clearing dispenser by middle clicking"""
        for i, dispenser in enumerate(self.dispensers):
            if dispenser[:2] == (x, y):
                if dispenser[3] == 1:
                    self.dispensers[i] = (x, y, dispenser[2], 0)
                    self.grid[x][y][0].config(image=self.checked_image)
                else:
                    self.dispensers[i] = (x, y, dispenser[2], 1)
                    self.grid[x][y][0].config(image=self.clearing_image)
                break

    def set_rt(self, time):
        self.run_time = time

def start(root):
    child = tk.Toplevel(root)
    set_title_and_icon(child, "Playerless Core Tools")

    child.configure(bg=colours.bg)
    child.size = (int(RSF*300), int(RSF*325))

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
