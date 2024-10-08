"""Calculates distribution of fungus, and bone meal usage, \nfor a given grid of nylium, and placement and fire order of dispensers"""

import math
import time
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as font
from PIL import Image, ImageDraw, ImageTk

from src.Assets import colours
from src.Assets.constants import RSF
import src.Assets.constants as const
from src.Assets.helpers import ToolTip, set_title_and_icon, export_custom_heatmaps, resource_path
from src.Fungus_Distribution_Backend import calc_huge_fungus_distribution, \
    calculate_fungus_distribution, output_viable_coords
from src.Stochastic_Optimisation import start_optimisation, optimise_all

# Testing notes
# - Run tests on 5x5 and 4x5 for num dispensers 1-5, cycles = 3 to see where the optimal solution
#   does or does not include cleare dispensers
# Keep an eye out during future patches for the wart block and bone meal calc values going
# inaccurate after optimising a bunch

# Non-linear scaling 
NLS = 1.765
WDTH = 92
HGHT = 46
PAD = 5
RAD = 26
DP = 5
MAX_SIDE_LEN = 20
WARPED = 0
CRIMSON = 1
UNCLEARED = 0

class SlideSwitch(tk.Canvas):
    def __init__(self, parent, callback=None, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)

        self.configure(width=WDTH, height=HGHT)
        self.configure(highlightthickness=0)
        self.configure(bg=colours.bg)
        self.fungus_type = tk.StringVar(value="warped")

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
            self.fungus_type.set("warped")
        else:
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.crimson)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, 3 * WDTH//4, HGHT//2)
            self.fungus_type.set("crimson")

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
        self.blocked_blocks = []
        self.nylium_type = tk.StringVar(value="warped")
        self.run_time = tk.StringVar(value="7")
        self.blast_chamber_effic = tk.StringVar(value="1")
        self.vars = []
        self.output_text_label = {}
        self.output_text_value = {}
        self.info_text_label = {}
        self.info_text_value = {}
        self.selected_block = ()
        self.just_all_optimised = False

        clearing_path = resource_path("src/Images/cleared_dispenser.png")
        self.clearing_image = tk.PhotoImage(file=clearing_path)
        self.clearing_image = self.clearing_image.subsample(3, 3)

        # Create a Canvas and Scrollbar 1055
        self.canvas = tk.Canvas(master, width=int(RSF*760), height=int(RSF*1055), bg=colours.bg)
        
        self.scrollbar = tk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create the scrollable frame inside the canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=colours.bg)
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind the scrollable region update to the frame configuration changes
        self.scrollable_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.resize_frame)

        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

        # Now, call your method to create widgets within the scrollable_frame
        self.create_widgets()

        # Create menu
        self.create_menu()

    def update_scroll_region(self, event):
        """Update the scrollable region based on the contents of the frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def resize_frame(self, event):
        """Make sure the frame size matches the canvas width."""
        self.canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def _on_mouse_wheel(self, event):
        # Get the current scroll position
        current_scroll_position = self.canvas.yview()
        
        # Limit values, e.g., preventing the upper scroll to be less than 0.1 (10% down from top)
        min_scroll = 0   # Set your desired upper limit
        max_scroll = 1.0   # Maximum scroll value corresponds to the bottom-most position

        # Calculate the new scroll position based on mouse wheel delta
        new_scroll_position = current_scroll_position[0] + (-1 * (event.delta / 120) / 10)  # Adjust sensitivity by changing /10

        # Check and enforce the scroll limits
        if new_scroll_position < min_scroll:
            self.canvas.yview_moveto(min_scroll)
        elif new_scroll_position > max_scroll:
            self.canvas.yview_moveto(max_scroll)
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_menu(self):
        """Setup the menu for the application."""
        toolbar = tk.Menu(self.master)
        self.master.config(menu=toolbar)

        file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.destroy)
        file_menu.add_command(label="Export Custom Heatmaps", command=self.export_heatmaps)

        help_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="What's this Tool For?", command=self.show_info_message)
        help_menu.add_command(label="How to Use this Tool", command=self.show_use_message)
        help_menu.add_command(label="Advanced Features", command=self.show_advanced_features)

        config_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        config_menu.add_command(label="Calibrate Run Time", command=self.calibrate_run_time)
        toolbar.add_cascade(label="Config", menu=config_menu)

        run_time_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="Run Time", menu=run_time_menu)
        for time in [1, 4, 7, 10, 15, 30, 60, 300, 1000]:
            run_time_menu.add_radiobutton(
                label=str(time).rjust(5), 
                variable=self.run_time, 
                value=time,
                command=lambda time1=time: self.set_rt(time1)
            )

        bc_effic_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="Blast Chamber Efficiency", menu=bc_effic_menu)
        for effic in [0.0, 0.5, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]:
            bc_effic_menu.add_radiobutton(
                label=(str(round(100 * effic)) + "%").rjust(5), 
                variable=self.blast_chamber_effic, 
                value=effic,
                command=lambda effic1=effic: self.set_bce(effic1)
            )

        # Set default CPU iteration time for the simulated annealing algorithm
        file_path = resource_path("cpu_benchmark.txt")
        with open(file_path, "a+") as f:
            # Move the cursor to the start of the file
            f.seek(0)
            data = f.readline().strip()
            if not data:
                f.seek(0)
                f.write(f"{const.BASE_CPU_ITER_TIME}\n")

    def calibrate_run_time(self):
        """Runs a benchmark optimisation test to measure user's processing speed and modify cooling rate accordingly"""
        # Run test with 4 uncleared dispensers, 3 times
        disp_coords = [(0, 0, UNCLEARED) for _ in range(0, 4)]
        num_tests = 3
        des_run_time = 15

        for i in range(0, num_tests):
            start_time = time.time()
            f = open(resource_path("cpu_benchmark.txt"), "r+")
            _, _, iterations = start_optimisation(
                disp_coords,
                5, # Default 5x5 nylium platform
                5,
                120, # High val for wart block efficiency
                WARPED,
                des_run_time, # Desired run time of 15 secs
                1, # 1 Cycle
                [] # No blocked blocks
            )

            total_iter_time = (time.time() - start_time)
            time_diff_percent = 100 * (total_iter_time - des_run_time) / des_run_time
            time_per_iter = total_iter_time / iterations

            f.write(str(time_per_iter))
            f.close()

            print(f"Calibration loop {i} run time misalignment: {time_diff_percent}%")
            print(f"Iteration time: {time_per_iter}\n")


    def set_bce(self, effic):
        """Change the blast chamber efficiency (default is 100%)"""
        self.blast_chamber_effic.set(effic)
        self.calculate()
        self.display_block_info()

    def show_info_message(self):
        """Provide some information to the user about what this tool is used for"""
        messagebox.showinfo(
            "Information",
            "This tool is used to optimise the placement of dispensers on a platform of nylium "
            "such that their position and ordering maximises fungus production, whilst not exceeding "
            "a given bone meal efficiency requirement.",
            icon='question'
        )

    def show_use_message(self):
        """Provide some information to the user about how to use this tool"""
        messagebox.showinfo(
            "Information",
            "Each playerless nether tree farm core uses a platform of nylium with 1 or more " 
            "dispensers directly bone-mealing it to produce fungi.\n\n"
            "To begin, set the length and width of your nylium platform using the sliders.\n\n"
            "Then, set the amount of cycles the dispensers are triggered for before the core "
            "resets, using the cycles slider.\n\n"
            "Finally, place down your dispensers by left clicking on the nylium blocks, and view "
            "fungus and foliage distribution metrics in the outputs section at the bottom.",
            icon='info'
        )

    def show_advanced_features(self):
        """Provide some information to the user about how to use this tool"""
        messagebox.showinfo(
            "Information",
            "Change nylium types using the slide switch.\n\n"
            "To find the optimal dispenser placement for the provided wart block efficiency, "
            "click the optimise button. Note this will strictly optimise with cleared dispensers "
            "if you have any.\n\n"
            "To export custom huge fungus heatmaps based off the fungus distribution of the nylium "
            "grid, click the export button.\n\n"
            "To place a cleared dispenser, or mark a nylium block for non-growth, middle-click or "
            "ctrl+left click on a dispenser or nylium block respectively.\n\n"
            "To view growth statistics of a specific block and/or dispenser, right-click on the "
            "block.\n\n"
            "To reset the grid, click the reset button, and to reset the sliders, double-click on "
            "them.",
            icon='info'
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

        # Create images for the checked and unchecked, and blocked states
        checked_path = resource_path("src/Images/dispenser.png")
        unchecked_path = resource_path("src/Images/warped_nylium.png")
        blocked_path = resource_path("src/Images/blocked_block.png")
        self.checked_image = tk.PhotoImage(file=checked_path)
        self.unchecked_image = tk.PhotoImage(file=unchecked_path)
        self.blocked_image = tk.PhotoImage(file=blocked_path)

        # Resize the images
        self.checked_image = self.checked_image.subsample(3, 3)
        self.unchecked_image = self.unchecked_image.subsample(3, 3)
        self.blocked_image = self.blocked_image.subsample(3, 3)

        self.create_sliders()

        self.button_slider_frame = tk.Frame(self.scrollable_frame, bg=colours.bg)
        self.button_slider_frame.pack(pady=10)  

        self.reset_button = tk.Button(self.button_slider_frame, text="Reset", command=self.reset_grid, font=small_button_font, bg=colours.warped)
        self.reset_button.pack(side=tk.RIGHT, padx=5)

        self.nylium_switch = SlideSwitch(self.button_slider_frame, callback=self.update_nylium_type)
        self.nylium_switch.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid_frame = tk.Frame(self.scrollable_frame, bg=colours.bg)
        self.grid_frame.pack(pady=5)

        self.optimise_button = tk.Button(self.scrollable_frame, text="Optimise", command=self.optimise,
                                         font=large_button_font, bg=colours.crimson, pady=2)
        self.optimise_button.pack(pady=5)
        self.optimise_button.bind("<Button-2>", lambda event: self.fe_optimise_all())
        self.optimise_button.bind("<Control-Button-1>", lambda event: self.fe_optimise_all())


        self.export_button = tk.Button(self.scrollable_frame, text="Export", command=self.export_heatmaps,
                                         font=large_button_font, bg=colours.aqua_green,
                                         pady=2, padx=16)
        self.export_button.pack(pady=5)

        self.master_frame = tk.Frame(self.scrollable_frame)
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
        self.master_frame = tk.Frame(self.scrollable_frame)
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
        cycles_tooltip = ToolTip(self.cycles_label, (
                        "Set how many times the dispensers are activated."))
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
        wb_effic_tooltip = ToolTip(self.wb_effic_label, (
                        "Restrict optimal solutions to require a certain bone meal\n"
                        "(or ~8 composted wart blocks) per fungus produced efficiency."))
        self.wb_effic_slider = tk.Scale(
            self.slider_frame, 
            from_=20, 
            to=120, 
            orient=tk.HORIZONTAL, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250,
            resolution=0.1
        )
        self.wb_effic_slider.set(120)
        self.wb_effic_slider.bind("<Double-Button-1>", lambda event: self.reset_slider(event, 120))
        self.wb_effic_slider.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")      

    def reset_slider(self, event, default=5):
        self.scrollable_frame.after(10, lambda: event.widget.set(default))
    
    def update_nylium_type(self, nylium_type=None):
        if nylium_type == WARPED:
            self.nylium_type.set("warped")
            unchecked_path = resource_path("src/Images/warped_nylium.png")
        elif nylium_type == CRIMSON:
            self.nylium_type.set("crimson")
            unchecked_path = resource_path("src/Images/crimson_nylium.png")
        elif self.nylium_type.get() == "warped":
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
                if self.vars[i][j].get() == 0 and (i, j) not in self.blocked_blocks:
                    tile[0].config(image=self.unchecked_image)
        self.calculate()
        self.display_block_info()

    def create_ordered_dispenser_array(self, rows, cols):
        """Create a 2D array of dispensers ordered by the time they were placed on the grid"""
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
            # Preserve initial time value and cleared status
            dispenser_array[x][y] = (i + 1, dispenser[2], dispenser[3])

        return dispenser_array
    
    def update_grid(self, _):
        """Update the grid based on the slider values"""
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
        blocked_copy = self.blocked_blocks.copy()
        self.blocked_blocks = []

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
                # Middle-click to set to a clearing dispenser or blocked block
                # depending on if clicked block is a dispenser or nylium block
                cb.bind("<Button-2>", lambda event, x=i, y=j: self.set_cleared_or_blocked(x, y))
                # Accesible ctrl+right click option for users without a mouse/middle-click
                cb.bind("<Control-Button-1>", lambda event, x=i, y=j: self.set_cleared_or_blocked(x, y))

                var_row.append(var)
                row.append((cb, None))
                # Restore the state of the checkbox, if it existed before
                if i < len(saved_states) and j < len(saved_states[i]):
                    var.set(saved_states[i][j])
                    if saved_states[i][j] == 1:
                        cleared = dispenser_array[i][j][2]
                        if cleared == 1:
                            cb.config(image=self.clearing_image)
                        else:
                            cb.config(image=self.checked_image)
                        label = tk.Label(self.grid_frame, text=str(dispenser_array[i][j][0]), font=label_font)
                        label.grid(row=i, column=j, padx=0, pady=0, sticky='se')
                        row[j] = (cb, label)
                        self.dispensers.append((i, j, dispenser_array[i][j][1], cleared))
                    if (i, j) in blocked_copy:
                        cb.config(image=self.blocked_image)
                        self.blocked_blocks.append((i, j))
            self.grid.append(row)
            self.vars.append(var_row)

        self.calculate()
        self.display_block_info()

    def add_dispenser(self, x, y, cleared=False):
        """Add a dispenser to the nylium grid at the given coordinates"""
        label_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*5))

        # Toggle the state of the checkbox
        self.vars[x][y].set(not self.vars[x][y].get())
        if (x, y) in self.blocked_blocks:
            self.blocked_blocks.remove((x, y))

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

    def reset_grid(self, remove_blocked=True):
        """Reset the nyliium grid to its initial state"""
        for i, row in enumerate(self.grid):
            for j, tile in enumerate(row):
                self.vars[i][j].set(0)
                tile[0].config(image=self.unchecked_image)
                if isinstance(tile[1], tk.Label):
                    tile[1].destroy()
                # need to remove blocked blocks that are overlapped by a dispenser
                # give a warning or something to let user know optimising doesnt and wont support blocked blocks
        if remove_blocked:
            self.blocked_blocks = []  
        else:
            for x, y in self.blocked_blocks:
                self.grid[x][y][0].config(image=self.blocked_image)

        self.dispensers = []
        self.calculate()
        self.display_block_info()

    def optimise(self):
        """Optimise the placement of dispensers on the nylium grid"""
        # Ignore button press if it was special clicked for optimising all parameters
        if (self.just_all_optimised == True):
            self.just_all_optimised = False
            return

        fungus_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        disp_coords = [(d[0], d[1], d[3]) for d in self.dispensers]
        if len(disp_coords) == 0:
            return

        optimal_coords, optimal_value, _ = start_optimisation(
            disp_coords,
            self.col_slider.get(), 
            self.row_slider.get(),
            self.wb_effic_slider.get(),
            fungus_type,
            self.run_time.get(),
            self.cycles_slider.get(),
            self.blocked_blocks
        )

        if optimal_coords == -1:
            messagebox.showwarning("Error", "Maximum runtime exceeded.")
            return
        elif ([-1, -1, UNCLEARED] in optimal_coords or len(optimal_coords) == 0):
            messagebox.showinfo(
                "Optimisation Notice",
                "No optimal solution found for\n"
                "given wart block efficiency."
            )
            return
        self.reset_grid(remove_blocked=False)
        # print("optimall: ", optimal_coords, "back")
        for disp_coord in optimal_coords:
            self.add_dispenser(disp_coord[0], disp_coord[1], disp_coord[2])
        # Generate a list of other viable coords that are as optimal or within 0.1% of the most
        # optimal found solution, storing them in an external file
        result = output_viable_coords(
            optimal_coords, 
            optimal_value, 
            self.col_slider.get(),
            self.row_slider.get(),
            self.wb_effic_slider.get(),
            fungus_type,
            self.cycles_slider.get(),
            self.blocked_blocks
        )
        if isinstance(result, (int, float)) and not isinstance(result, BaseException):
            n = len(disp_coords)
            # 8 transformations for a square grid, 4 for a rectangular grid
            transforms = 8 if self.col_slider.get() == self.row_slider.get() else 4
            trimmed_string = (
                f"\n\nNote {transforms * math.factorial(n) - 8:,} possible alternate "
                "placements (permutations of firing order) were trimmed "
                "for computational reasons."
            )            
            messagebox.showinfo(f"Success", 
                                f"Successfully exported {result} alternate "
                                f"placement{'s' if result != 1 else ''} to viable_coords.txt."
                                f"{trimmed_string if n > 8 else ''}")
        else:
            error_message = f"An error has occurred:\n{result}"
            if not error_message.endswith(('.', '!', '?')):
                error_message += '.'
            messagebox.showwarning("Export Error", error_message)      
    
    def fe_optimise_all(self):
        """Optimise all paramters relating to a playerless nether tree farm core using simulated annealing"""
        self.just_all_optimised = True
        result, optimal_value, iterations = optimise_all()
        print("All optimised results:", result)
        print("Optimal value:", optimal_value)
        print("Iterations:", iterations)
        self.cycles_slider.set(result['num_cycles'])
        self.col_slider.set(result['width'])
        self.row_slider.set(result['length'])
        self.update_nylium_type(result['fungus_type'])
        self.update_grid(iterations)
        self.reset_grid(remove_blocked=True)
        
        for disp_coord in result['disp_layout']:
            self.add_dispenser(disp_coord[1], disp_coord[0], disp_coord[2])

    def export_heatmaps(self):
        """Export custom heatmaps based on the fungus distribution of the nylium grid"""
        self.dispensers.sort(key=lambda d: d[2])
        dispenser_coordinates = [(d[0], d[1], d[3]) for d in self.dispensers]
        fungus_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED   
        # Calculate fungus distribution     
        disp_des_fungi_grids = \
            calculate_fungus_distribution(
                self.col_slider.get(), 
                self.row_slider.get(),
                len(dispenser_coordinates),
                dispenser_coordinates,
                fungus_type,
                self.cycles_slider.get(),
                self.blocked_blocks
            )["disp_des_fungi_grids"]

        result = export_custom_heatmaps(
            self.col_slider.get(),
            self.row_slider.get(),
            np.sum(disp_des_fungi_grids, axis=(0,1))
        )

        if result == 0:
            messagebox.showinfo("Success", "Heatmaps successfully exported to weighted_fungi_heatmap.xlsx")
        else:
            error_message = f"An error has occurred:\n{result}"
            if not error_message.endswith(('.', '?', '!')):
                error_message += '.'
            messagebox.showwarning("Export Error", error_message)

    def calculate(self):
        """Calculate the fungus distribution and bone meal usage for the nylium grid"""
        self.dispensers.sort(key=lambda d: d[2])
        dispenser_coordinates = [(d[0], d[1], d[3]) for d in self.dispensers]
        fungus_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        # Calculate fungus distribution
        dist_data = calculate_fungus_distribution(
            self.col_slider.get(), 
            self.row_slider.get(),
            len(dispenser_coordinates),
            dispenser_coordinates,
            fungus_type,
            self.cycles_slider.get(),
            self.blocked_blocks
        )
        
        total_foliage = dist_data["total_foliage"]
        total_des_fungi = dist_data["total_des_fungi"]
        bm_for_prod = dist_data["bm_for_prod"]
        bm_for_grow = dist_data["bm_for_grow"]
        bm_total = dist_data["bm_total"]
        total_wart_blocks, *_ = calc_huge_fungus_distribution(
            self.row_slider.get(),
            self.col_slider.get(),
            fungus_type,
            dispenser_coordinates,
            self.cycles_slider.get(),
            self.blocked_blocks,
            self.blast_chamber_effic.get()
        )

        output_labels = [
            f"Total {'Warped' if fungus_type == WARPED else 'Crimson'} Fungi",
            "Bone Meal to Produce a Fungus",
            "Bone Meal for Production",
            "Bone Meal for Growth",
            "Total Foliage",
            "Total Wart Blocks",
            "Net Bone Meal"
        ]

        output_values = [
            round(total_des_fungi, DP),
            round(bm_for_prod / total_des_fungi, DP) if total_des_fungi != 0 else 0.0,
            round(bm_for_prod, DP),
            round(bm_for_grow, DP),
            round(total_foliage, DP),
            round(total_wart_blocks, DP),
            round(total_wart_blocks / const.WARTS_PER_BM - bm_total, DP),
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
        
        bm_for_prod_tooltip = ToolTip(self.output_text_label[2], (
                        "Bone meal spent by the nylium dispensers that creates the fungi.\n"
                        "Factors in 75% of bone meal retrieved from composting excess foliage."))
        
        bm_for_growth_tooltip = ToolTip(self.output_text_label[3],(
                        "Bone meal spent on growing already produced fungi."))
        
        net_bm_tooltip = ToolTip(self.output_text_label[6],(
                        "Surplus bone meal after 1 global cycle of the core and subsequent harvest.\n"
                        "Takes bone meal from composted wart blocks minus production and growth bm."))
        
        # Create the labels for output values
        for i, output_value in enumerate(output_values):
            # Create a label for the output value
            value_label = tk.Label(self.output_frame, text=output_value, bg=colours.bg, fg=colours.fg, font=output_font)
            value_label.grid(row=i + 2, column=1, padx=PAD, pady=PAD, sticky="WE")
            value_label.grid_columnconfigure(0, weight=1)  # Ensure the label fills the cell horizontally

            # Store the value label in the dictionary for later use
            self.output_text_value[i] = value_label
    
    def display_block_info(self, x=None, y=None):
        """Display the growth statistics of a specific block and/or dispenser"""
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
        dispenser_coordinates = [(d[0], d[1], d[3]) for d in self.dispensers]
        fungus_type = CRIMSON if self.nylium_type.get() == "crimson" else WARPED
        cycles = self.cycles_slider.get()
        dist_data = calculate_fungus_distribution(
            self.col_slider.get(), 
            self.row_slider.get(),
            len(dispenser_coordinates),
            dispenser_coordinates,
            fungus_type,
            cycles,
            self.blocked_blocks
        )
        disp_foliage_grids = dist_data["disp_foliage_grids"]
        disp_des_fungi_grids = dist_data["disp_des_fungi_grids"]
        
        info_labels = [
            f"{'Warped' if fungus_type == WARPED else 'Crimson'} Fungi at {(x,y)}",
            f"Foliage at {(x,y)}",
        ]
        sel_fungi_amount = np.sum(disp_des_fungi_grids, axis=(0,1))[x, y]
        sel_foliage_amount = np.sum(disp_foliage_grids, axis=(0,1))[x, y] - sel_fungi_amount
        info_values = [
            round(sel_fungi_amount, DP),
            round(sel_foliage_amount, DP)
        ]

        # If selected block is a dispenser, include additional info
        if any((x, y) == coord[:2] for coord in dispenser_coordinates):
            index = next(i for i, coord in enumerate(dispenser_coordinates) if (x, y) == coord[:2])
            bone_meal_used = 0
            for c in range(cycles):
                # First sum only earlierly ordered dispensers affect the current one
                if c == 0:
                    if index == 0:
                        cycle_sum = np.zeros((self.row_slider.get(), self.col_slider.get()))
                    else:
                        cycle_sum = np.sum(disp_foliage_grids[:index, c, :, :], axis=0)
                else:
                    cycle_sum = np.sum(disp_foliage_grids[:, :c, :, :], axis=(0, 1))
                    cycle_sum += np.sum(disp_foliage_grids[:index, c, :, :], axis=0)
                bone_meal_used += 1 - cycle_sum[x, y]


            info_labels.append(f"{'Warped' if fungus_type == WARPED else 'Crimson'} Fungi Produced")
            info_labels.append("Bone Meal Used")
            info_labels.append("Bone Meal per Fungi")
            info_labels.append("Position")
            info_labels.append("Cleared")

            fungi_produced = np.sum(disp_des_fungi_grids[index])
            info_values.append(round(fungi_produced, DP))
            info_values.append(round(bone_meal_used, DP))
            info_values.append(round(bone_meal_used / fungi_produced, DP))
            info_values.append(f'{index + 1}')
            info_values.append(f'{"Yes" if self.dispensers[index][3] == 1 else "No"}')

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
        for i, info_value in enumerate(info_values):
            label = tk.Label(self.output_frame, text=info_value, bg=colours.bg, fg=colours.fg, font=output_font)
            label.grid(row=i + 2, column=3, padx=PAD, pady=PAD, sticky="WE")
            label.grid_columnconfigure(0, weight=1)  # Ensure the label fills the cell horizontally

            # Store the value label in the dictionary for later use
            self.info_text_value[i] = label
        
        foliage_tooltip = ToolTip(self.output_text_label[1], "All other foliage generated at this position (excluding desired fungi).")
        
    def set_cleared_or_blocked(self, x, y):
        """Set a dispenser to a clearing dispenser by middle clicking or nylium to a blocked block"""
        if self.vars[x][y].get() == 0:
            # Toggle block between blocked and unblocked
            if (x, y) in self.blocked_blocks:
                self.blocked_blocks.remove((x, y))
                self.grid[x][y][0].config(image=self.unchecked_image)
            else:
                self.blocked_blocks.append((x, y))
                self.grid[x][y][0].config(image=self.blocked_image)
        else: 
            for i, dispenser in enumerate(self.dispensers):
                if dispenser[:2] == (x, y):
                    if dispenser[3] == 1:
                        self.dispensers[i] = (x, y, dispenser[2], 0)
                        self.grid[x][y][0].config(image=self.checked_image)
                    else:
                        self.dispensers[i] = (x, y, dispenser[2], 1)
                        self.grid[x][y][0].config(image=self.clearing_image)
                    break

        self.calculate()
        self.display_block_info()
        return "break"

    def set_rt(self, time):
        """Set the run time of the optimisation algorithm."""
        self.run_time.set(time)

def start(root):
    """Start the Playerless Core Tools program."""
    
    child = tk.Toplevel(root)
    set_title_and_icon(child, "Playerless Core Tools")

    child.configure(bg=colours.bg)
    child.size = (int(RSF*1), int(RSF*1))

    # Get the root window's position and size
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()

    # Position the child window to the top right of the root window
    child.geometry(f"+{root_x + root_width}+{root_y}")

    # Update the window so it actually appears in the correct position
    child.update_idletasks()

    app = App(child)
    child.mainloop()
    
