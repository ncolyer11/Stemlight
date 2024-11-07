"""Calculates distribution of fungus, and bone meal usage, \nfor a given grid of nylium, and placement and fire order of dispensers"""

import math
import time
import psutil

import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as font
from PIL import Image, ImageDraw, ImageTk

from src.Assets import colours
from src.Assets.constants import *
from src.Assets.data_classes import *
from src.Assets.helpers import ToolTip, set_title_and_icon, export_custom_heatmaps, resource_path, \
    show_custom_message, program_window_counter, all_program_instances
from src.Playerless_Core_Tools_Backend import calc_huge_fungus_distribution, \
    calculate_fungus_distribution, output_viable_coords
from src.Stochastic_Optimisation import start_optimisation

# Testing notes
# - Run tests on 5x5 and 4x5 for num dispensers 1-5, cycles = 3 to see where the optimal solution
#   does or does not include cleare dispensers

# TODO:
# fix bug where worst case without caring about order takes into account all layouts, not strictly different orderings
# move nylium switch and reset button to be on the same level as the optimise and heatmap button
# move calibrate run time into the file menu and maybe consider a new algo for it
# run time and blast effic labels dont show upon start and after importing
#   - this doesn't matter too much though as these will become message boxes in the future probs

#################
### CONSTANTS ###
#################

# General settings
DEFAULT_RUN_TIME = 7
MAX_UPDATE_SCHEDULE_DELAY = 750
INIT_UPDATES = 2
SLIDER_MAX_CYCLES = 5

# Scaling and geometry
NLS = 1.765 # Non-linear scaling factor
WDTH = 92
HGHT = 46
PAD = 5
RAD = 26
DP = 5
MAX_SIDE_LEN = 20
DEFAULT_SIDE_LEN = 5

# Display and performance
BASELINE_CLK_SPEED = 2000
WINDOW_HEIGHT = 997

# Timing values
RUN_TIME_VALS = [1, 4, 7, 10, 15, 30, 60, 300, 1000]

# Efficiency values
BC_EFFIC_VALS = [0.0, 0.5, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]

###########################
### CLASSES & FUNCTIONS ###
###########################
class SlideSwitch(tk.Canvas):
    def __init__(self, parent, callback=None, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)

        self.configure(width=WDTH, height=HGHT)
        self.configure(highlightthickness=0)
        self.configure(bg=colours.bg)
        self.nylium_type = WARPED

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

    def toggle(self, event=None):
        if self.state:
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.warped)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, WDTH//4, HGHT//2)
            self.nylium_type = WARPED
        else:
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.crimson)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, 3 * WDTH//4, HGHT//2)
            self.nylium_type = CRIMSON

        self.state = not self.state
        if self.callback:
            self.callback()

    def assign(self, state):
        if state == WARPED:
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.warped)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, WDTH//4, HGHT//2)
            self.state = False
        else:
            self.new_image = self.create_squircle(WDTH, HGHT, RAD, colours.crimson)
            self.itemconfig(self.rect, image=self.new_image)
            self.coords(self.oval, 3 * WDTH//4, HGHT//2)
            self.state = True
    
    def create_squircle(self, width, height, radius, fill):
        # Create a new image with transparent background
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        # Create a rounded rectangle on the image
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([(0, 0), (width, height)], 
                               radius=radius, fill=fill, outline=colours.bg)

        return ImageTk.PhotoImage(image)

class App:
    ######################
    ### INITIALISATION ###
    ######################
    def __init__(self, master, window_id, layout_info: PlayerlessCore):
        self.master = master                        # The TopLevel window
        self.window_id = window_id
        self.L = layout_info                        # All properties of the playerless core itself
        self.D = DisplayInfo({}, {}, {}, {}, ())    # Start with all empty labels and info values
        
        self.grid = []          # Stores the checkbox objects themselves
        self.checkboxes = []    # 2D array of checkboxes to store the state of each dispenser
        self.updates = 0        # Track if the layout has been loaded after starting the program
        self.update_job = None  # Track the latest scheduled layout/grid update/calculation job

        self.init_gui()
    
    def init_gui(self):
        self.clearing_image = tk.PhotoImage(file=resource_path("src/Images/cleared_dispenser.png"))
        self.clearing_image = self.clearing_image.subsample(3, 3)

        # Add main GUI elements
        self.canvas = tk.Canvas(self.master, height=int(RSF * WINDOW_HEIGHT), bg=colours.bg)
        self.create_scroll_bar()
        self.create_widgets()
        self.create_menu()
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def create_scroll_bar(self):
        self.scrollbar = tk.Scrollbar(self.master, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=colours.bg)

        # Bind the scrollable region update to the frame configuration changes
        self.scrollable_frame.bind("<Configure>", self.update_scroll_region)
        # Create the scrollable frame inside the canvas
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame,
                                                             anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        # Bind mouse wheel scrolling
        self.master.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def create_menu(self):
        """Setup the menu for the application."""
        toolbar = tk.Menu(self.master)
        self.master.config(menu=toolbar)

        file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.destroy)
        file_menu.add_command(label="Import Layout", command=self.import_layout)
        file_menu.add_command(label="Export Layout", command=self.export_layout)
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
        for time in RUN_TIME_VALS:
            run_time_menu.add_radiobutton(
                label=str(time).rjust(5), 
                variable=self.L.run_time, 
                value=time,
                command=lambda time1=time: self.set_rt(time1)
            )

        bc_effic_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
        toolbar.add_cascade(label="Blast Chamber Efficiency", menu=bc_effic_menu)
        for effic in BC_EFFIC_VALS:
            bc_effic_menu.add_radiobutton(
                label=(str(round(100 * effic)) + "%").rjust(5), 
                variable=self.L.blast_chamber_effic, 
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
                f.write(f"{BASE_CPU_ITER_TIME}\n")

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
        self.button_slider_frame.pack(pady=5)  

        self.reset_button = tk.Button(self.button_slider_frame, text="Reset",
                                      command=self.reset_grid, font=small_button_font,
                                      bg=colours.dark_orange, padx=10, pady=5)
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        self.reset_button.bind("<Shift-Button-1>", self.reset_all)

        self.nylium_switch = SlideSwitch(self.button_slider_frame, callback=self.update_nylium_type)
        self.nylium_switch.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid_frame = tk.Frame(self.scrollable_frame, bg=colours.bg)
        self.grid_frame.pack(pady=5)

        # Create a new frame to contain the buttons
        button_frame = tk.Frame(self.scrollable_frame, bg=colours.bg)
        button_frame.pack()

        self.additional_property_button = tk.Button(button_frame, text="Optimise",
                                                    command=self.optimise, font=large_button_font,
                                                    bg=colours.crimson, pady=2)
        self.additional_property_button.pack(side=tk.LEFT, padx=5)
        self.additional_property_button.bind("<Button-2>", self.debug_button)
        self.additional_property_button.bind("<Control-Button-1>", self.debug_button)

        self.heatmap_button = tk.Button(button_frame, text="Heatmap", command=self.export_heatmaps,
                                        font=large_button_font, bg=colours.aqua_green, pady=2)
        self.heatmap_button.pack(side=tk.LEFT, padx=5, pady=10)

        self.master_frame = tk.Frame(self.scrollable_frame)
        self.master_frame.pack()

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
        self.block_info_title = tk.Label(self.output_frame, text="Block Stats\t",
                                         font=output_title_font,
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
        row_label = tk.Label(self.slider_frame, text="Length:", bg=colours.bg, fg=colours.fg,
                             font=slider_font)
        row_label.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
        self.row_slider = tk.Scale(
            self.slider_frame, 
            from_=1, 
            to=MAX_SIDE_LEN, 
            orient=tk.HORIZONTAL, 
            command=self.update_layout_vals, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.row_slider.set(5)
        self.row_slider.bind("<Double-Button-1>", self.reset_slider)
        self.row_slider.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        col_label = tk.Label(self.slider_frame, text="Width:", bg=colours.bg, fg=colours.fg,
                             font=slider_font)
        col_label.grid(row=0, column=1, padx=5, pady=0, sticky="nsew")
        self.col_slider = tk.Scale(
            self.slider_frame, 
            from_=1, 
            to=MAX_SIDE_LEN, 
            orient=tk.HORIZONTAL, 
            command=self.update_layout_vals, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.col_slider.set(5)
        self.col_slider.bind("<Double-Button-1>", self.reset_slider)
        self.col_slider.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.cycles_label = tk.Label(self.slider_frame, text="No. Cycles:", bg=colours.bg, 
                                     fg=colours.fg, font=slider_font)
        self.cycles_label.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        ToolTip(self.cycles_label, ("Set how many times the dispensers are activated."))
        self.cycles_slider = tk.Scale(
            self.slider_frame, 
            from_=1, 
            to=SLIDER_MAX_CYCLES,
            orient=tk.HORIZONTAL, 
            command=self.update_layout_vals, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.cycles_slider.set(1)
        self.cycles_slider.bind("<Double-Button-1>", lambda event: self.reset_slider(event, 1))
        self.cycles_slider.grid(row=3, column=0, padx=5, sticky="nsew")

        self.wb_per_fungus_label = tk.Label(self.slider_frame, text="Wart Blocks/Fungus:", 
                                       bg=colours.bg, fg=colours.fg, font=slider_font)
        self.wb_per_fungus_label.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")
        ToolTip(self.wb_per_fungus_label, (
                                   "Restrict optimal solutions to require a certain bone meal\n"
                                   "(or ~8 composted wart blocks) per fungus produced efficiency."))
        self.wb_per_fungus_slider = tk.Scale(
            self.slider_frame, 
            from_=20, 
            to=120, 
            orient=tk.HORIZONTAL, 
            command=self.update_layout_vals,
            bg=colours.bg, 
            fg=colours.fg, 
            length=250,
            resolution=0.1
        )
        self.wb_per_fungus_slider.set(120)
        self.wb_per_fungus_slider.bind("<Double-Button-1>",
                                       lambda event: self.reset_slider(event, 120))
        self.wb_per_fungus_slider.grid(row=3, column=1, padx=5, sticky="nsew")

    ################
    ### FEATURES ###
    ################
    def optimise(self):
        """Optimise the placement of dispensers on the nylium grid"""
        if self.L.num_disps == 0:
            return

        L_optimise = PlayerlessCore(
            num_disps=self.L.num_disps,
            disp_coords=self.L.disp_coords,
            size=self.L.size,
            nylium_type=self.L.nylium_type,
            cycles=self.L.cycles,
            blocked_blocks=self.L.blocked_blocks,
            wb_per_fungus=self.L.wb_per_fungus,
            blast_chamber_effic=self.L.blast_chamber_effic,
            run_time=self.L.run_time,
            additional_property=False
        )
        optimal_coords, optimal_value, iterations = start_optimisation(L_optimise)

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
        for disp_coord in optimal_coords:
            self.add_dispenser(disp_coord.row, disp_coord.col, disp_coord.cleared)
        # Generate a list of other viable coords that are as optimal or within 0.1% of the most
        # optimal found solution, storing them in an external file
        self.print_viable_coords(output_viable_coords(self.L, optimal_coords, optimal_value))

    def calculate(self, dist_data=None):
        """Calculate the fungus distribution and bone meal usage for the nylium grid"""

        # Calculate fungus distribution if not provided
        if dist_data is None:
            dist_data = calculate_fungus_distribution(self.L)

        total_foliage = dist_data.total_foliage
        total_des_fungi = dist_data.total_des_fungi
        bm_for_prod = dist_data.bm_for_prod
        bm_for_grow = dist_data.bm_for_grow
        bm_total = dist_data.bm_total
        total_wart_blocks, *_ = calc_huge_fungus_distribution(self.L, dist_data)

        output_labels = [
            f"Total {'Warped' if self.L.nylium_type== WARPED else 'Crimson'} Fungi",
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
            round(total_wart_blocks / WARTS_PER_BM - bm_total, DP),
        ]

        label_font = font.Font(family='Segoe UI', size=int((RSF**NLS)*9))
        output_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))

        # Clear existing labels
        for label in self.D.output_label.values():
            label.destroy()
        self.D.output_label = {}

        for value_label in self.D.output_value.values():
            value_label.destroy()
        self.D.output_value = {}

        # Create the labels for outputs
        for i, label_text in enumerate(output_labels):
            # Create a label for the output
            label = tk.Label(self.output_frame, text=label_text, bg=colours.bg, fg=colours.fg,
                             font=label_font)
            label.grid(row=i + 2, column=0, padx=PAD, pady=PAD, sticky="W")

            # Store the label in the dictionary for later use
            self.D.output_label[i] = label
        
        ToolTip(self.D.output_label[2], (
                "Bone meal spent by the nylium dispensers that creates the fungi.\n"
                "Factors in 75% of bone meal retrieved from composting excess foliage."))
        
        ToolTip(self.D.output_label[2], (
                "Bone meal spent by the nylium dispensers that creates the fungi.\n"
                "Factors in 75% of bone meal retrieved from composting excess foliage."))

        ToolTip(self.D.output_label[4],(
                "Total foliage produced excluding sprouts and desired fungi."))
        
        ToolTip(self.D.output_label[6],(
                "Surplus bone meal after 1 global cycle of the core and subsequent harvest.\n"
                "Takes bone meal from composted wart blocks minus production and growth bm."))
        
        # Create the labels for output values
        for i, output_value in enumerate(output_values):
            # Create a label for the output value
            value_label = tk.Label(self.output_frame, text=output_value, bg=colours.bg,
                                   fg=colours.fg, font=output_font)
            value_label.grid(row=i + 2, column=1, padx=PAD, pady=PAD, sticky="WE")
            # Ensure the label fills the cell horizontally
            value_label.grid_columnconfigure(0, weight=1)

            # Store the value label in the dictionary for later use
            self.D.output_value[i] = value_label
    
    def set_cleared_or_blocked(self, row, col):
        """Set a dispenser to a clearing dispenser by middle clicking or nylium to a blocked 
        block"""
        if self.checkboxes[row][col].get() == 0:
            # Toggle block between blocked and unblocked
            if (row, col) in self.L.blocked_blocks:
                self.L.blocked_blocks.remove((row, col))
                self.grid[row][col][0].config(image=self.unchecked_image)
            else:
                self.L.blocked_blocks.append((row, col))
                self.grid[row][col][0].config(image=self.blocked_image)
        else: 
            for i, dispenser in enumerate(self.L.disp_coords):
                if (dispenser.row, dispenser.col) == (row, col):
                    if dispenser.cleared == CLEARED:
                        self.L.disp_coords[i] = Dispenser(row, col, dispenser.timestamp, UNCLEARED)
                        self.grid[row][col][0].config(image=self.checked_image)
                    else:
                        self.L.disp_coords[i] = Dispenser(row, col, dispenser.timestamp, CLEARED)
                        self.grid[row][col][0].config(image=self.clearing_image)
                    break
        self.L.num_disps = len(self.L.disp_coords)

        self.schedule_layout_calcs_and_grid_update(update_grid=False)
        return "break" # Prevents the default behaviour of the middle click apparently

    def remove_selected_block(self):
        """Remove the currently selected block"""
        self.D.selected_block = ()
        self.remove_labels(self.D.info_label)
        self.remove_labels(self.D.info_value)

    #############
    ### UI/UX ###
    #############
    def add_dispenser(self, row, col, cleared=False):
        """
        Add a dispenser to the nylium grid at the given coordinates
        """
        label_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*5))
        # Toggle the state of the checkbox
        self.checkboxes[row][col].set(not self.checkboxes[row][col].get())
        if (row, col) in self.L.blocked_blocks:
            self.L.blocked_blocks.remove((row, col))

        # Update the image based on the state of the checkbox
        if self.checkboxes[row][col].get() == 0:
            self.grid[row][col][0].config(image=self.unchecked_image)
            new_dispensers = []
            for d in self.L.disp_coords:
                if (d.row, d.col) != (row, col):
                    new_dispensers.append(d)
                    # Reorder dispensers after removing one in the middle
                    label = tk.Label(self.grid_frame, text=len(new_dispensers), font=label_font)
                    d_row = d.row
                    d_col = d.col
                    label.grid(row=d_row, column=d_col, padx=0, pady=0, sticky='se')  
                    self.grid[d_row][d_col][1].destroy()
                    # Update the grid with the label
                    self.grid[d_row][d_col] = (self.grid[d_row][d_col][0], label) 

            self.L.disp_coords = [d for d in self.L.disp_coords if (d.row, d.col) != (row, col)]
            self.grid[row][col][1].destroy()
        else:
            if cleared == True:
                self.grid[row][col][0].config(image=self.clearing_image)
                self.L.disp_coords.append(Dispenser(row, col, time.time(), CLEARED))
            else:
                self.grid[row][col][0].config(image=self.checked_image)
                self.L.disp_coords.append(Dispenser(row, col, time.time(), UNCLEARED))
            label = tk.Label(self.grid_frame, text=str(len(self.L.disp_coords)), font=label_font)
            # Place label in the bottom right corner
            label.grid(row=row, column=col, padx=0, pady=0, sticky='se')  
            # Update the grid with the label
            self.grid[row][col] = (self.grid[row][col][0], label)  
        self.L.num_disps = len(self.L.disp_coords)

        self.schedule_layout_calcs_and_grid_update(update_grid=False)

    def reset_grid(self, remove_blocked=True):
        """Reset the nyliium grid to its initial state"""
        for i, row in enumerate(self.grid):
            for j, tile in enumerate(row):
                self.checkboxes[i][j].set(0)
                tile[0].config(image=self.unchecked_image)
                if isinstance(tile[1], tk.Label):
                    tile[1].destroy()
        if remove_blocked:
            self.L.blocked_blocks = []  
        else:
            for row, col in self.L.blocked_blocks:
                self.grid[row][col][0].config(image=self.blocked_image)

        self.L.disp_coords = []
        self.L.num_disps = 0
        dist_data = self.display_block_info()
        self.calculate(dist_data)

    def reset_all(self, event):
        """Reset the grid and sliders to their default values"""
        self.reset_grid()
        self.row_slider.set(DEFAULT_SIDE_LEN)
        self.col_slider.set(DEFAULT_SIDE_LEN)
        self.cycles_slider.set(1)
        self.wb_per_fungus_slider.set(120)
        self.update_nylium_type(WARPED)
        self.nylium_switch.assign(WARPED)
        self.update_layout_vals()
        dist_data = self.display_block_info()
        self.calculate(dist_data)

    def display_block_info(self, row=None, col=None) -> PlayerlessCoreOutput:
        """Display the growth statistics of a specific block and/or dispenser"""
        length = self.L.size.length
        width = self.L.size.width
        sel_block_row = 0 if not self.D.selected_block else self.D.selected_block[0]
        sel_block_col = 0 if not self.D.selected_block else self.D.selected_block[1]
        
        # Return if no block is selected
        if not self.D.selected_block and row == None:
            return
        # Calling with empty arguments simply updates the currently selected block
        elif row is None and col is None:
            row, col = self.D.selected_block
            # Reset selected block if it is out of bounds
            if row >= length or col >= width or sel_block_row >= length or sel_block_col >= width:
                return self.remove_selected_block()
                
        # Rest selected block if it's already selected (toggling it)
        elif (row, col) == self.D.selected_block:
            return self.remove_selected_block()
        # Default behaviour is to just select a new block
        else:
            self.D.selected_block = (row, col)
        
        dist_data = calculate_fungus_distribution(self.L)
        disp_foliage_grids = dist_data.disp_foliage_grids
        disp_des_fungi_grids = dist_data.disp_des_fungi_grids
        
        info_labels = [
            f"{'Warped' if self.L.nylium_type == WARPED else 'Crimson'} Fungi at {(row, col)}",
            f"Foliage at {(row,col)}",
        ]

        sel_fungi_amount = np.sum(disp_des_fungi_grids, axis=(0,1))[row, col]
        sel_foliage_amount = np.sum(disp_foliage_grids, axis=(0,1))[row, col] - sel_fungi_amount
        info_values = [
            round(sel_fungi_amount, DP),
            round(sel_foliage_amount, DP)
        ]

        # If selected block is a dispenser, include additional info
        if any((row, col) == (coord.row, coord.col) for coord in self.L.disp_coords):
            index = next(i for i, coord in enumerate(self.L.disp_coords) \
                         if (row, col) == (coord.row, coord.col))
            bone_meal_used = 0
            for cycle in range(self.L.cycles):
                # First sum only earlierly ordered dispensers affect the current one
                if cycle == 0:
                    if index == 0:
                        cycle_sum = np.zeros((self.row_slider.get(), self.col_slider.get()))
                    else:
                        cycle_sum = np.sum(disp_foliage_grids[:index, cycle, :, :], axis=0)
                else:
                    cycle_sum = np.sum(disp_foliage_grids[:, :cycle, :, :], axis=(0, 1))
                    cycle_sum += np.sum(disp_foliage_grids[:index, cycle, :, :], axis=0)
                bone_meal_used += 1 - cycle_sum[row, col]

            info_labels.append(f"{'Warped' if self.L.nylium_type == WARPED else 'Crimson'} "
                               f"Fungi Produced")
            info_labels.append("Bone Meal Used")
            info_labels.append("Bone Meal per Fungi")
            info_labels.append("Position")
            info_labels.append("Cleared")

            fungi_produced = np.sum(disp_des_fungi_grids[index])
            info_values.append(round(fungi_produced, DP))
            info_values.append(round(bone_meal_used, DP))
            info_values.append(round(bone_meal_used / fungi_produced, DP))
            info_values.append(f'{index + 1}')
            info_values.append(f'{"Yes" if self.L.disp_coords[index].cleared == CLEARED else "No"}')

        label_font = font.Font(family='Segoe UI', size=int((RSF**NLS)*9))
        output_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*9))

        # Clear existing labels
        for label in self.D.info_label.values():
            label.destroy()
        self.D.info_label = {}

        for value_label in self.D.info_value.values():
            value_label.destroy()
        self.D.info_value = {}

        # Create the labels for info labels
        for i, label_text in enumerate(info_labels):
            label = tk.Label(self.output_frame, text=label_text, bg=colours.bg, fg=colours.fg, 
                             font=label_font)
            label.grid(row=i + 2, column=2, padx=PAD, pady=PAD, sticky="W")

            # Store the label in the dictionary for later use
            self.D.info_label[i] = label
        
        ToolTip(self.D.info_label[1],
                "All other foliage generated at this position (excluding desired fungi).")

        # Create the labels for block info values
        for i, info_value in enumerate(info_values):
            label = tk.Label(self.output_frame, text=info_value, bg=colours.bg, fg=colours.fg, 
                             font=output_font)
            label.grid(row=i + 2, column=3, padx=PAD, pady=PAD, sticky="WE")
            label.grid_columnconfigure(0, weight=1)  # Ensure the label fills the cell horizontally

            # Store the value label in the dictionary for later use
            self.D.info_value[i] = label
            
        return dist_data

    def reset_slider(self, event, default=5):
        self.scrollable_frame.after(10, lambda: event.widget.set(default))

    def set_bce(self, effic):
        """Change the blast chamber efficiency (default is 100%)"""
        self.L.blast_chamber_effic = effic
        dist_data = self.display_block_info()
        self.calculate(dist_data)

    def set_rt(self, time):
        """Set the run time of the optimisation algorithm."""
        self.L.run_time = time

    ######################
    ### INPUT & OUTPUT ###
    ######################
    def import_layout(self):
        """Import a layout from a yaml file"""
        file_path = tk.filedialog.askopenfilename(
            title="Import Layout",
            initialdir="layouts",
            filetypes=(("YAML files", "*.yaml"), ("All files", "*.*"))
        )
        if file_path:
            self.L = PlayerlessCore.from_yaml(file_path)
            print(f"\nLayout imported from {file_path}")
            self.update_ui_elements()
            self.update_layout_vals()

    def export_layout(self):
        """Export the current layout to a yaml file"""
        file_path = tk.filedialog.asksaveasfilename(
            title="Export Layout",
            initialdir="layouts",
            defaultextension=".yaml",
            filetypes=(("YAML files", "*.yaml"), ("All files", "*.*"))
        )
        if file_path:
            self.L.to_yaml(file_path)
            print(f"Layout exported to {file_path}")

    def calibrate_run_time(self):
        """Runs a benchmark optimisation test to measure user's processing speed and modify 
        cooling rate accordingly"""
        # Run test with 4 uncleared dispensers, 3 times
        disp_coords = [Dispenser(0, 0, t, UNCLEARED) for t in range(0, 4)]
        num_tests = 3
        des_run_time = 15

        for i in range(0, num_tests):
            start_time = time.time()
            f = open(resource_path("cpu_benchmark.txt"), "r+")
            L_calibrate = PlayerlessCore(
                disp_coords=disp_coords,
                size=Dimensions(5, 5),
                nylium_type=WARPED,
                cycles=1,
                blocked_blocks=[],
                wb_per_fungus=120,
                blast_chamber_effic=1.0,
                run_time=des_run_time,
                additional_property=True
            )
            _, _, iterations = start_optimisation(L_calibrate)

            total_iter_time = (time.time() - start_time)
            time_diff_percent = 100 * (total_iter_time - des_run_time) / des_run_time
            time_per_iter = total_iter_time / iterations

            f.write(str(time_per_iter))
            f.close()

            print(f"Calibration loop {i} run time misalignment: {time_diff_percent}%")
            print(f"Iteration time: {time_per_iter}\n")
    
    def export_heatmaps(self):
        """Export custom heatmaps based on the fungus distribution of the nylium grid"""
        # Calculate fungus distribution     
        disp_des_fungi_grids = calculate_fungus_distribution(self.L).disp_des_fungi_grids

        result = export_custom_heatmaps(
            self.col_slider.get(),
            self.row_slider.get(),
            np.sum(disp_des_fungi_grids, axis=(0,1))
        )

        if result == 0:
            messagebox.showinfo("Success",
                                "Heatmaps successfully exported to weighted_fungi_heatmap.xlsx")
        else:
            error_message = f"An error has occurred:\n{result}"
            if not error_message.endswith(('.', '?', '!')):
                error_message += '.'
            messagebox.showwarning("Export Error", error_message)
            
    def print_viable_coords(self, result) -> int | float | BaseException:
        if isinstance(result, (int, float)) and not isinstance(result, BaseException):
            # 8 transformations for a square grid, 4 for a rectangular grid
            transforms = 8 if self.col_slider.get() == self.row_slider.get() else 4
            trimmed_string = (
                f"\n\nNote {transforms * math.factorial(self.L.num_disps) - 8:,} possible "
                "alternate placements (permutations of firing order) were trimmed "
                "for computational reasons."
            )
            file_path = "Alternate Dispenser Placements.txt"
            message = (
                f"Successfully exported {result} alternate "
                f"placement{'s' if result != 1 else ''} to {file_path}."
                f"{trimmed_string if self.L.num_disps > 8 else ''}"
            )
            show_custom_message(
                title="Success",
                message=message,
                file_path=file_path,
                open_button_colour=colours.aqua_green,
                close_button_colour=colours.crimson,
                bg_colour=colours.bg,
                fg_colour=colours.fg,
                fg_button_colour=None
            )
        else:
            error_message = f"An error has occurred:\n{result}"
            if not error_message.endswith(('.', '!', '?')):
                error_message += '.'
            messagebox.showwarning("Export Error", error_message) 

    ################
    ### UPDATERS ###
    ################
    def update_scroll_region(self, event):
        """Update the scrollable region based on the contents of the frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=event.width)

    def resize_frame(self, event):
        """Make sure the frame size matches the canvas width."""
        # Get the width of the canvas
        canvas_width = event.width if event else self.canvas.winfo_width()
        # Set the scrollable frame width to match the canvas width
        self.canvas.itemconfig(self.scrollable_frame_id, width=canvas_width)

    def _on_mouse_wheel(self, event):
        # Check if the current window has focus
        # Using the walrus operator to assign and check the value of the current focused instance
        if (instance := self.get_focus_instance(event)) is not None:
            # Check if the focused widget is the canvas
            # Get the current scroll position
            current_scroll_position = instance.canvas.yview()

            # Limit values, e.g., preventing the upper scroll to be less than 0.1 (10% down from top)
            min_scroll = 0   # Set your desired upper limit
            max_scroll = 1.0   # Maximum scroll value corresponds to the bottom-most position

            # Calculate the new scroll position based on mouse wheel delta
            new_scroll_position = current_scroll_position[0] + (-1 * (event.delta / 120) / 10)

            # Check and enforce the scroll limits
            if new_scroll_position < min_scroll:
                instance.canvas.yview_moveto(min_scroll)
            elif new_scroll_position > max_scroll:
                instance.canvas.yview_moveto(max_scroll)
            else:
                instance.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_focus_instance(self, event):
        for window_id, instance in all_program_instances.items():
            if instance.master == event.widget.winfo_toplevel():
                return instance
            
        return None
    
    def update_ui_elements(self):
        self.row_slider.set(self.L.size.length)
        self.col_slider.set(self.L.size.width)
        self.cycles_slider.set(self.L.cycles)
        self.wb_per_fungus_slider.set(self.L.wb_per_fungus)
        self.update_nylium_type(self.L.nylium_type, skip_calc=True)
        self.nylium_switch.assign(self.L.nylium_type)
        self.nylium_switch.nylium_type = self.L.nylium_type

    def update_layout_vals(self, _=None):
        """Update layout values and schedule update_grid if not loaded."""
        self.L.size = Dimensions(self.row_slider.get(), self.col_slider.get())
        self.L.cycles = self.cycles_slider.get()
        self.L.wb_per_fungus = self.wb_per_fungus_slider.get()
        self.L.nylium_type = self.nylium_switch.nylium_type

        # Load the layout once on program start without double updating the grid
        if self.updates == 0:
            self.update_grid(None, save_dispensers=False)
            self.schedule_layout_calcs_and_grid_update(update_grid=False)
        elif self.updates <= INIT_UPDATES:
            self.schedule_layout_calcs_and_grid_update(update_grid=False)
        else:
            self.schedule_layout_calcs_and_grid_update()
        
        self.updates += 1
         
    def schedule_layout_calcs_and_grid_update(self, update_grid=True):
        """Schedule update_grid to run in 1 second, canceling any previous schedules."""
        # Cancel the previous scheduled job, if it exists
        if self.update_job is not None:
            self.master.after_cancel(self.update_job)

        # Schedule update_grid to run in 1 second
        schedule_delay = self.get_update_schedule_delay()
        self.update_job = self.master.after(schedule_delay, self.run_update_job, update_grid)

    def update_grid(self, _, save_dispensers=True):
        """Update the grid based on the slider values"""
        # Save the states of the checkboxes
        if save_dispensers:
            saved_states = [[cb.get() for cb in cb_row] for cb_row in self.checkboxes]
        else:
            coords = [(disp.row, disp.col) for disp in self.L.disp_coords]
            saved_states = [
                    [1 if (i, j) in coords else 0
                    for j in range(self.L.size.width)]
                for i in range(self.L.size.length)
            ]
        rows = self.L.size.length
        cols = self.L.size.width
        # Create a 2D array of dispensers ordered by the time they were placed on the grid
        # Excludes dispensers that are out of bounds
        dispenser_array = self.create_ordered_dispenser_array(rows, cols)

        # Remove all the checkboxes and labels from the grid
        for row in self.grid:
            for cb, label in row:
                cb.destroy()
                if isinstance(label, tk.Label):
                    label.destroy()
        
        # Reset the grid and checkboxes
        self.grid = []
        self.checkboxes = []
        # Save the blocked blocks coordinates whilst clearing them and the dispenser coords
        blocked_copy = self.L.blocked_blocks.copy()
        self.L.blocked_blocks = []
        self.L.disp_coords = []

        for row in range(rows):
            cb_row = np.zeros(cols, dtype=object)
            var_row = np.zeros(cols, dtype=object)
            for col in range(cols):
                var = tk.IntVar()
                var.set(0)
                cb = self.create_cb(row, col)
                var_row[col] = var
                cb_row[col] = (cb, None)

                # Restore the state of the checkbox, if it existed before
                # or fill in a new dispenser array
                if row < len(saved_states) and col < len(saved_states[row]):
                    self.restore_cb(cb, var, row, col, cb_row, saved_states, dispenser_array,
                                    blocked_copy)

            self.grid.append(cb_row)
            self.checkboxes.append(var_row)
        self.L.num_disps = len(self.L.disp_coords)

    def update_nylium_type(self, nylium_type: NyliumType | None = None, skip_calc: bool = False):
        """
        Update the nylium type and the images of the checkboxes.\n
        Params:
            nylium_type: The nylium type to set the grid to, defaults to warped
        """
        # Set the nylium type to the specified type
        if nylium_type == WARPED:
            self.L.nylium_type = WARPED
            unchecked_path = resource_path("src/Images/warped_nylium.png")
        elif nylium_type == CRIMSON:
            self.L.nylium_type = CRIMSON
            unchecked_path = resource_path("src/Images/crimson_nylium.png")
        # If the nylium type is not specified, toggle the current nylium type
        elif self.L.nylium_type == WARPED:
            self.L.nylium_type = CRIMSON
            unchecked_path = resource_path("src/Images/crimson_nylium.png")
        elif self.L.nylium_type == CRIMSON:
            self.L.nylium_type = WARPED
            unchecked_path = resource_path("src/Images/warped_nylium.png")
        else:
            raise ValueError("Layout contains an invalid nylium type")
        self.unchecked_image = tk.PhotoImage(file=unchecked_path)
        self.unchecked_image = self.unchecked_image.subsample(3, 3)
        # Update the images of the checkboxes
        for i, row in enumerate(self.grid):
            for j, tile in enumerate(row):
                if self.checkboxes[i][j].get() == 0 and (i, j) not in self.L.blocked_blocks:
                    tile[0].config(image=self.unchecked_image)
        if not skip_calc:
            dist_data = self.display_block_info()
            self.calculate(dist_data)

    ###############
    ### HELPERS ###
    ###############
    def debug_button(self, event):
        self.L.print_values()
        print()

    def run_update_job(self, update_grid):
        """Updates """
        if update_grid:
            self.update_grid(None, save_dispensers=False)
        dist_data = self.display_block_info()
        self.calculate(dist_data)
       
    def remove_labels(self, labels):
        """Remove the labels from the grid."""
        for label in labels.values():
            label.destroy()
        labels = {}

    def get_update_schedule_delay(self) -> int:
        """
        Calculates roughly how long to delay calculations and focus on GUI updates
        given the size and type of the grid, number of dispensers, and cycles.
        Also adjusts the delay based on the CPU speed or number of cores.
        """
        delay_time = self.L.cycles * self.L.size.length * self.L.size.width * self.L.num_disps
        
        fungi_multiplier = 1.0 if self.L.nylium_type == CRIMSON else 1.15  # Crimson runs quicker
        delay_time *= fungi_multiplier

        # Get some system performance factor
        cpu_frequency = psutil.cpu_freq().current  # Current CPU frequency in MHz

        system_performance_factor = cpu_frequency / BASELINE_CLK_SPEED
        delay_time = round(min(MAX_UPDATE_SCHEDULE_DELAY, delay_time) / system_performance_factor)
        return delay_time
    
    def show_info_message(self):
        """Provide some information to the user about what this tool is used for"""
        messagebox.showinfo(
            "Information",
            "This tool is used to optimise the placement of dispensers on a platform of nylium "
            "such that their position and ordering maximises fungus production, whilst not "
            "exceeding a given bone meal efficiency requirement.",
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

    def restore_cb(self, cb, var, row, col, cb_row, saved_states, dispenser_array, blocked_copy):
        label_font = font.Font(family='Segoe UI Semibold', size=int((RSF ** NLS) * 5))
        var.set(saved_states[row][col])
        if saved_states[row][col] == 1:
            cleared = dispenser_array[row][col][2]
            if cleared == CLEARED:
                cb.config(image=self.clearing_image)
            else:
                cb.config(image=self.checked_image)

            label = tk.Label(self.grid_frame, text=str(dispenser_array[row][col][0]),
                             font=label_font)
            label.grid(row=row, column=col, padx=0, pady=0, sticky='se')
            cb_row[col] = (cb, label)
            self.L.disp_coords.append(Dispenser(row, col, dispenser_array[row][col][1], cleared))
        
        if (row, col) in blocked_copy:
            cb.config(image=self.blocked_image)
            self.L.blocked_blocks.append((row, col))

    def create_cb(self, row, col) -> tk.Button: 
        cb = tk.Button(
            self.grid_frame,
            image=self.unchecked_image,
            borderwidth=0,
            highlightthickness=0,
            bd=1,
            bg=colours.phtalo_green,
            command=lambda row_l=row, col_l=col: self.add_dispenser(row_l, col_l)
        )
        cb.grid(row=row, column=col, padx=0, pady=0)
        # Right-click to view individual block info
        cb.bind("<Button-3>",
                lambda event, row_l=row, col_l=col: self.display_block_info(row_l, col_l))
        # Middle-click to set to a clearing dispenser or blocked block
        # depending on if clicked block is a dispenser or nylium block
        cb.bind("<Button-2>",
                lambda event, row_l=row, col_l=col: self.set_cleared_or_blocked(row_l, col_l))
        # Accesible ctrl+right click option for users without a mouse/middle-click
        cb.bind("<Control-Button-1>",
                lambda event, row_l=row, col_l=col: self.set_cleared_or_blocked(row_l, col_l))
        return cb

    def create_ordered_dispenser_array(self, rows, cols):
        """Create a 2D array of dispensers ordered by the time they were placed on the grid"""
        # Sort the dispensers list by the time data
        sorted_dispensers: List[Dispenser] = sorted(
            self.L.disp_coords, key=lambda dispenser: dispenser.timestamp
        )
        # Filter out only valid dispensers
        filtered_dispensers: List[Dispenser] = [
            d for d in sorted_dispensers if d.row < rows and d.col < cols
        ]

        # Create a 2D array with the same dimensions as self.checkboxes, initialized with zeros
        dispenser_array = [[(0, 0, 0) for _ in range(cols)] for _ in range(rows)]
        # Iterate over the sorted dispensers list
        for i, dispenser in enumerate(filtered_dispensers):
            # The order of the dispenser is i + 1
            # Set the corresponding element in the dispenser array to i + 1
            row, col = dispenser.row, dispenser.col
            # Preserve initial time value and cleared status
            dispenser_array[row][col] = (i + 1, dispenser.timestamp, dispenser.cleared)

        return dispenser_array

#############
### START ###
#############
def start(root):
    """Start the Playerless Core Tools program."""
    global program_window_counter
    program_window_counter += 1
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
    L = PlayerlessCore(
        num_disps=0,
        disp_coords=[],
        size=Dimensions(DEFAULT_SIDE_LEN, DEFAULT_SIDE_LEN),
        nylium_type=WARPED,
        cycles=1,
        blocked_blocks=[],
        wb_per_fungus=120,
        blast_chamber_effic=1.0,
        run_time=DEFAULT_RUN_TIME,
        additional_property=False
    )
    app = App(child, program_window_counter, L)  # Pass the unique ID to the instance
    all_program_instances[program_window_counter] = app  # Track the instance

    child.mainloop()
