import os
import sys
import time
import itertools

import xlsxwriter
import numpy as np
import tkinter as tk
from tkinter import font

from litemapy import Schematic

from src.Assets import heatmap_data
from src.Assets.constants import *
from src.Assets.version import version
from src.Assets.data_classes import PlayerfulCoreOutput, Dimensions

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

program_window_counter = 0
all_program_instances = {}

VALID_ENCODING_BLOCKS = {'minecraft:red_concrete', 'minecraft:blue_concrete',
                         'minecraft:cyan_concrete','minecraft:light_blue_concrete'}
STEMS_SHEET_IDX = 0
SHROOMS_SHEET_IDX = 1

class ToolTip:
    def __init__(self, widget, tooltip_text):
        self.widget = widget
        self.tooltip_text = tooltip_text
        self.tip_window = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)  # Dismiss on click

        # Delay timer variable
        self.timer = None

    def enter(self, event):
        if self.tip_window:
            return  # Do not create a new tooltip if one already exists
        # Use a timer to delay showing the tooltip
        self.timer = self.widget.after(500, self.show_tip, event.x_root, event.y_root)  # 500 ms delay

    def leave(self, event):
        if self.timer:
            self.widget.after_cancel(self.timer)  # Cancel the timer if leaving
            self.timer = None
        self.hide_tip()

    def show_tip(self, x, y):
        "Display text in a tooltip window"
        if self.tip_window or not self.tooltip_text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        main_font = font.Font(family='Segoe UI', size=int((RSF**1.765)*8))

        label = tk.Label(tw, text=self.tooltip_text, justify=tk.CENTER,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=main_font)
        label.pack(ipadx=1)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def set_title_and_icon(root, program_name, skip_prg_name=False):
    """Set the title and icon of the tkinter window"""
    version_string = f"Stemlight{version}: "
    root.title(f"{'' if skip_prg_name else version_string}"
               f"{program_name}")
    try:
        # Try to use the .ico file
        icon_path = resource_path('src/Assets/icon.ico')
        root.iconbitmap(icon_path)
    except:
        # If that fails, try to use the .xbm file
        try:
            icon_path = resource_path('src/Assets/icon.xbm')
            root.iconbitmap('@' + icon_path)
        except:
            pass  # If that also fails, don't bother setting an icon

def show_custom_message(title, message, file_path, open_button_colour, close_button_colour,
                        bg_colour, fg_colour, fg_button_colour):
    def open_file():
        os.startfile(file_path)
        dialog.destroy()

    dialog = tk.Toplevel()
    dialog.title(title)
    set_title_and_icon(dialog, title, skip_prg_name=True)
    
    dialog.configure(bg=bg_colour)
    
    # Create a label to measure the required size
    label = tk.Label(dialog, text=message, wraplength=350, bg=bg_colour, fg=fg_colour)
    label.pack(pady=10)
    
    # Update the dialog to get the required size
    dialog.update_idletasks()
    width = max(400, label.winfo_reqwidth() + 20)  # Add some padding
    height = max(200, label.winfo_reqheight() + 100)  # Add some padding for buttons
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    # Repack the label to adjust to the new size
    label.pack_forget()
    label.pack(pady=10)

    button_frame = tk.Frame(dialog, bg=bg_colour)
    button_frame.pack(pady=10)

    open_button = tk.Button(button_frame, text="Open File", command=open_file,
                            bg=open_button_colour, fg=fg_button_colour)
    open_button.pack(side=tk.LEFT, padx=5)

    close_button = tk.Button(button_frame, text="Close", command=dialog.destroy,
                             bg=close_button_colour, fg=fg_button_colour)
    close_button.pack(side=tk.LEFT, padx=5)

    dialog.transient()  # Make the dialog a transient window
    dialog.grab_set()  # Require the user to answer the message box before continuing
    dialog.wait_window(dialog)  # Wait for the dialog to close

def get_cell_value(sheet_name, row_number, column_number):
    """Return the value of the cell at the given row and column in the given sheet."""
    return heatmap_data.heatmap_array[sheet_name][row_number][column_number]

def export_custom_heatmaps(p: Dimensions, des_fungi_grid):
    """
    Export the custom nether tree heatmap data, generated\n 
    from the dispenser placements, to an Excel file.
    Params:
    - p: Dimensions object containing the dimensions of the platform
    - des_fungi_grid: 2D array of the des fungi grid
    """
    try:
        outSheet = []
        outWorkbook = xlsxwriter.Workbook(r"weighted_fungi_heatmap.xlsx")
        start_time = time.time()
        
        hf = Dimensions(
            NT_MAX_RAD + p.length + NT_MAX_RAD,
            NT_MAX_RAD + p.width + NT_MAX_RAD
        )
        hf_grids = np.zeros((
            len(BLOCK_TYPES) + 1, 
            hf.length,
            hf.width,
            NT_MAX_HT
        ))
    
        # Iterate through each x,z coord in the nylium grid/platform 
        for nylium_x, nylium_z in itertools.product(range(p.width), range(p.length)):
            # Generation order is Stems -> Shrooms -> Warts
            for b in range(len((BLOCK_TYPES))):
                fungus_chance = des_fungi_grid[nylium_x][nylium_z]
                # Iterate through each x,y,z coord relative to the fungi
                y_range, z_range, x_range = range(NT_MAX_HT), range(NT_MAX_WD), range(NT_MAX_WD)
                for y, z, x in itertools.product(y_range, z_range, x_range):
                    col = x + (NT_MAX_WD * z)
                    row = NT_MAX_HT - 1 - y
                    
                    weighted_chance = fungus_chance * get_cell_value(b, row, col)
                    curr = hf_grids[3][nylium_z + z][nylium_x + x][y]

                    gen_chance = (1 - curr) * weighted_chance
                    hf_grids[b][nylium_z + z][nylium_x + x][y] += gen_chance
                    hf_grids[3][nylium_z + z][nylium_x + x][y] += gen_chance

        # Write data to Excel file for each block type
        y_range, z_range, x_range = range(NT_MAX_HT), range(hf.width), range(hf.length)
        for b, block_type in enumerate(BLOCK_TYPES):   # 0 = stems, 1 = shrooms, 2 = vrm0/warts
            outSheet.append(outWorkbook.add_worksheet(block_type))
            for y, z, x in itertools.product(y_range, z_range, x_range):
                col = z + (hf.width * x)
                row = NT_MAX_HT - 1 - y
                heatmap_data_point = hf_grids[b][x][z][y]
                outSheet[b].write(row, col, heatmap_data_point)
                        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Heatmap data calculated and output to excel file in {elapsed_time} seconds")
        outWorkbook.close()
        return 0
    except Exception as e:
        print(f"Error occurred whilst exporting heatmaps: {e}")
        return e

def comp_probability(success_chance, attempts):
    """
    Calculate the probability of an event not happening after a given number of attempts."""
    return 1 - (1 - success_chance) ** attempts

def stems_and_shrooms(average_stems, average_shroomlights, 
                        row2, col2, hat_cycles2, trunk_cycles2):
    """
    Computes the instantaneous value of the average stems and shroomlights of the layout
    """
    average_stems += comp_probability(
        get_cell_value(0, row2, col2), trunk_cycles2) / trunk_cycles2  # 0: stem heatmap
    
    average_shroomlights += comp_probability(
        get_cell_value(1, row2, col2), hat_cycles2) / hat_cycles2 # 1: shroomlight heatmap
    
    return average_stems, average_shroomlights

def schem_layout_to_rates_data(path, hat_cycles, trunk_cycles):
    """A helper function that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a
    given nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to
    pre-calculated heatmaps in a .xlsx file to work out the average stems, shroomlights and wart blocks harvested per cycle
    for that nether tree farm layout"""
    
    # To fix empty input bug
    if path == '':
        path = resource_path('src/Assets/empty_layout.litematic')

    schem = Schematic.load(path)
    reg = list(schem.regions.values())[0]

    start_time = time.time()
    # Skipping unnecessary calculations if layout schematic is empty
    if schem == 'empty_layout.litematic':
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("\nElapsed time:", elapsed_time, "seconds")
        return 0, 0, 0, 0, 0, 0

    Xrange, Yrange, Zrange = reg.xrange(), reg.yrange(), reg.zrange()
    avg_shroomlights, avg_wart_blocks, avg_stems = 0, 0, 0
    valid_encoding_blocks = {'minecraft:red_concrete', 'minecraft:blue_concrete',
                             'minecraft:cyan_concrete', 'minecraft:light_blue_concrete'}
    for y in Yrange:
        for x in Xrange:
            for z in Zrange:
                block = reg.getblock(x, y, z)
                X, Y, Z = x, y, z
                if min(Xrange) < 0:
                    X += NT_MAX_WD - 1
                if min(Yrange) < 0:
                    Y += NT_MAX_HT - 1
                if min(Zrange) < 0:
                    Z += NT_MAX_WD - 1

                # 3D data is stored in 'slices' on a 2D spreadsheet, hence some math is needed to convert between them
                col = X + (NT_MAX_WD * Z)
                row = NT_MAX_HT - 1 - Y

                # Setting vrm value
                if block.blockid not in valid_encoding_blocks:
                    continue
                elif block.blockid == "minecraft:red_concrete":
                    vrm = 0
                elif block.blockid == "minecraft:blue_concrete":
                    vrm = 1
                elif block.blockid == "minecraft:cyan_concrete":
                    vrm = 2
                elif block.blockid == "minecraft:light_blue_concrete":
                    vrm = 3

                # Calculating stems and shroomlight values
                avg_stems, avg_shroomlights = stems_and_shrooms(
                    avg_stems, avg_shroomlights, row, col, hat_cycles, trunk_cycles)
                # Calculating wart block values
                if X == 0 and Z == 0:
                    avg_wart_blocks += comp_probability(
                        get_cell_value(vrm + 2, row, col), trunk_cycles) / trunk_cycles
                else:
                    avg_wart_blocks += comp_probability(
                        get_cell_value(vrm + 2, row, col), hat_cycles) / hat_cycles

    # Finding the efficiencies of the layout factoring in the varying cycles
    stem_E = (avg_stems / AVG_STEMS) / trunk_cycles
    shroomlight_E = (avg_shroomlights / AVG_SHROOMS) / hat_cycles
    wart_block_E = ((avg_wart_blocks / AVG_WARTS ** 2) * 
                    ((AVG_WARTS - AVG_TOP_WART) / hat_cycles + 
                    AVG_TOP_WART / trunk_cycles))

    print("Elapsed time:", time.time() - start_time, "seconds")

    return avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E

def get_cell_value(sheet_name2: str, row_number: int, column_number: int) -> float:
    """
    Return the value of the cell at the given row and column in the given sheet.
    """
    return heatmap_data.heatmap_array[sheet_name2][row_number][column_number]

def schem_layout_to_efficiency_and_vrms(path: str | None) -> PlayerfulCoreOutput:
    """
    A helper function that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a
    given nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to
    pre-calculated heatmaps in a python array to work out the average stems, shroomlights and wart blocks harvested per
    cycle for that nether tree farm layout.
    For more info on how this & the heatmaps were made visit the huge fungi huggers discord: https://discord.gg/EKKkyfcPPV
    """
    
    # To fix empty input bug
    if path == '':
        path = resource_path('src/Assets/empty_layout.litematic')
    schem = Schematic.load(path)
    reg = list(schem.regions.values())[0]

    # start tracking time
    start_time = time.time()

    # initialising values
    Xrange, Yrange, Zrange = reg.xrange(), reg.yrange(), reg.zrange()
    out = PlayerfulCoreOutput(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    for y in Yrange:
        for x in Xrange:
            for z in Zrange:
                block = reg.getblock(x, y, z)

                X, Y, Z = x, y, z
                if min(Xrange) < 0:
                    X += NT_MAX_WD - 1
                if min(Yrange) < 0:
                    Y += NT_MAX_HT - 1
                if min(Zrange) < 0:
                    Z += NT_MAX_WD - 1

                if block.blockid != "minecraft:air":
                    # 3D data is stored in a excel spreadsheet format in a 3D array,
                    # hence some math is needed to convert between them
                    col = X + (NT_MAX_WD * Z)
                    row = NT_MAX_HT - 1 - Y
                    if block.blockid not in VALID_ENCODING_BLOCKS:
                        continue
                    elif block.blockid == "minecraft:red_concrete":  # vrm 0
                        vrm = 2
                        if get_cell_value(vrm, row, col) > 0:
                            out.vrm0s += 1
                    elif block.blockid == "minecraft:blue_concrete":  # vrm 1
                        vrm = 3
                        if get_cell_value(vrm, row, col) > 0:
                            out.vrm1s += 1
                    elif block.blockid == "minecraft:cyan_concrete":  # vrm 2
                        vrm = 4
                        if get_cell_value(vrm, row, col) > 0:
                            out.vrm2s += 1
                    elif block.blockid == "minecraft:light_blue_concrete":  # vrm 3
                        vrm = 5
                        if get_cell_value(vrm, row, col) > 0:
                            out.vrm3s += 1
                    # calculating average stem, shroomlight and wart block values
                    out.avg_stems += get_cell_value(STEMS_SHEET_IDX, row, col)
                    out.avg_shrooms += get_cell_value(SHROOMS_SHEET_IDX, row, col)
                    out.avg_warts += get_cell_value(vrm, row, col)

    out.stems_effic = out.avg_stems / AVG_STEMS
    out.shrooms_effic = out.avg_shrooms / AVG_SHROOMS
    out.wb_per_fungus = out.avg_warts / AVG_WARTS
    # wart blocks max doesn't take into account vrm and the actual max warts including VRM is around 82 but that's infeasible in reality

    print(f"Elapsed time: {time.time() - start_time} seconds")
    return out

def create_dispenser_distribution(size):
    """Create the dispenser distribution matrix for foliage generated after bone-mealing nylium.
    \n Note that the matrix is padded with 0's surrounding the centred distribution for sizes > 5"""
    # Selection probabilities for blocks offset around a centred dispenser on a 5x5 grid of nylium
    sp = [
        0.10577931226910778, 0.20149313967509574,
        0.28798973593014715, 0.3660553272880777,
        0.4997510328685407, 0.6535605838853813
    ]
    
    dist_5x5 = np.array([
        [sp[0], sp[1], sp[2], sp[1], sp[0]],
        [sp[1], sp[3], sp[4], sp[3], sp[1]],
        [sp[2], sp[4], sp[5], sp[4], sp[2]],
        [sp[1], sp[3], sp[4], sp[3], sp[1]],
        [sp[0], sp[1], sp[2], sp[1], sp[0]],
    ])
    
    padded_dist = np.zeros((size, size))
    # Find the start indices for centering the 5x5 matrix within the SIZE x SIZE matrix
    offset = (size - 5) // 2
    # Insert the 5x5 matrix into the SIZE x SIZE matrix
    padded_dist[offset:offset+5, offset:offset+5] = dist_5x5
    
    return padded_dist