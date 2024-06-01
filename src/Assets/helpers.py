import os
import sys
import time
import itertools
import xlsxwriter
import numpy as np
import tkinter as tk
from tkinter import font
from litemapy import Schematic

from src.Assets import heatmap_data, constants as const
from src.Assets.version import version

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, tip_text, x, y):
        "Display text in a tooltip window"
        if self.tip_window or not tip_text:
            return
        x -= self.widget.winfo_width() // 2
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        main_font = font.Font(family='Segoe UI', size=int((const.RSF**1.765)*8))

        label = tk.Label(tw, text=tip_text, justify=tk.CENTER,
                    background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                    font=main_font)
        label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def set_title_and_icon(root, program_name):
    """Set the title and icon of the tkinter window"""
    root.title(f"Stemlight{version}: {program_name}")
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

def get_cell_value(sheet_name, row_number, column_number):
    """Return the value of the cell at the given row and column in the given sheet."""
    return heatmap_data.heatmap_array[sheet_name][row_number][column_number]

def export_custom_heatmaps(length, width, nyliumGrid):
    """Export the custom nether tree heatmap data, generated\n 
    from the dispenser placements, to an Excel file."""
    try:
        outSheet = []
        outWorkbook = xlsxwriter.Workbook(r"weighted_fungi_heatmap.xlsx")
        start_time = time.time()
        
        heatmap_length = const.NT_MAX_RAD + length + const.NT_MAX_RAD
        heatmap_width = const.NT_MAX_RAD + width + const.NT_MAX_RAD
        hf_grids = np.zeros((
            len(const.BLOCK_TYPES) + 1, 
            heatmap_length,
            heatmap_width,
            const.NT_MAX_HT
        ))
    
        # Iterate through each x,z coord in the nylium grid/platform 
        for nylium_x, nylium_z in itertools.product(range(width), range(length)):
            # Generation order is Stems -> Shrooms -> Warts
            for b, _ in enumerate(const.BLOCK_TYPES):  # 0 = stems, 1 = shrooms, 2 = vrm0/warts
                heatmap_weighting = nyliumGrid[nylium_x][nylium_z]
                y_range, z_range, x_range = range(const.NT_MAX_HT), range(const.NT_MAX_WD), range(const.NT_MAX_WD)
                # Iterate through each x,y,z coord relative to the fungi
                for y, z, x in itertools.product(y_range, z_range, x_range):
                    col = x + (const.NT_MAX_WD * z)
                    row = const.NT_MAX_HT - 1 - y
                    weighted_chance = heatmap_weighting * get_cell_value(b, row, col)

                    curr = hf_grids[3][nylium_z + z][nylium_x + x][y]
                    hf_grids[b][nylium_z + z][nylium_x + x][y] += (1 - curr) * weighted_chance
                    hf_grids[3][nylium_z + z][nylium_x + x][y] += hf_grids[b][nylium_z + z][nylium_x + x][y]

        # Write data to Excel file for each block type
        y_range, z_range, x_range = range(const.NT_MAX_HT), range(heatmap_width), range(heatmap_length)
        for b, block_type in enumerate(const.BLOCK_TYPES):
            outSheet.append(outWorkbook.add_worksheet(block_type))
            for y, z, x in itertools.product(y_range, z_range, x_range):
                col = z + (heatmap_width * x)
                row = const.NT_MAX_HT - 1 - y
                print(row, col)
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

    # Accessing a single element/cell in the above array
    def get_cell_value(sheet_name2, row_number, column_number):
        return heatmap_data.heatmap_array[sheet_name2][row_number][column_number]

    # Computes the instantaneous value of the avg stems and shroomlights of the layout
    def stems_and_shrooms(average_stems, average_shroomlights, 
                          row2, col2, hat_cycles2, trunk_cycles2):
        average_stems += comp_probability(
            get_cell_value(0, row2, col2), trunk_cycles2) / trunk_cycles2  # 0: stem heatmap
        
        average_shroomlights += comp_probability(
            get_cell_value(1, row2, col2), hat_cycles2) / hat_cycles2 # 1: shroomlight heatmap
        
        return average_stems, average_shroomlights

    # Calculates the complimentary probability of an event
    def comp_probability(success_chance, attempts):
        return 1 - (1 - success_chance) ** attempts

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
                    X += const.NT_MAX_WD - 1
                if min(Yrange) < 0:
                    Y += const.NT_MAX_HT - 1
                if min(Zrange) < 0:
                    Z += const.NT_MAX_WD - 1

                # 3D data is stored in 'slices' on a 2D spreadsheet, hence some math is needed to convert between them
                col = X + (const.NT_MAX_WD * Z)
                row = const.NT_MAX_HT - 1 - Y

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
    stem_E = (avg_stems / const.AVG_STEMS) / trunk_cycles
    shroomlight_E = (avg_shroomlights / const.AVG_SHROOMS) / hat_cycles
    wart_block_E = ((avg_wart_blocks / const.AVG_WARTS ** 2) * 
                    ((const.AVG_WARTS - const.AVG_TOP_WART) / hat_cycles + 
                    const.AVG_TOP_WART / trunk_cycles))

    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Elapsed time:", elapsed_time, "seconds")

    return avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E

def schem_layout_to_efficiency_and_vrms(path):
    """A helper function that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a
    given nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to
    pre-calculated heatmaps in a python array to work out the average stems, shroomlights and wart blocks harvested per
    cycle for that nether tree farm layout.
    For more info on how this & the heatmaps were made visit the huge fungi huggers discord: https://discord.gg/EKKkyfcPPV"""
    
    # To fix empty input bug
    if path == '':
        path = resource_path('src/Assets/empty_layout.litematic')
    schem = Schematic.load(path)
    reg = list(schem.regions.values())[0]

    # start tracking time
    start_time = time.time()

    # function for accessing a single value/cell in the above array
    def get_cell_value(sheet_name2, row_number, column_number):
        return heatmap_data.heatmap_array[sheet_name2][row_number][column_number]

    # initialising values
    Xrange, Yrange, Zrange = reg.xrange(), reg.yrange(), reg.zrange()
    avg_shroomlights, avg_wart_blocks, avg_stems, vrm0, vrm1, vrm2, vrm3 = 0, 0, 0, 0, 0, 0, 0
    valid_encoding_blocks = {'minecraft:red_concrete', 'minecraft:blue_concrete', 'minecraft:cyan_concrete',
                             'minecraft:light_blue_concrete'}

    for y in Yrange:
        for x in Xrange:
            for z in Zrange:
                block = reg.getblock(x, y, z)

                X, Y, Z = x, y, z
                if min(Xrange) < 0:
                    X += const.NT_MAX_WD - 1
                if min(Yrange) < 0:
                    Y += const.NT_MAX_HT - 1
                if min(Zrange) < 0:
                    Z += const.NT_MAX_WD - 1

                if block.blockid != "minecraft:air":
                    # 3D data is stored in a excel spreadsheet format in a 3D array,
                    # hence some math is needed to convert between them
                    col = X + (const.NT_MAX_WD * Z)
                    row = const.NT_MAX_HT - 1 - Y
                    if block.blockid not in valid_encoding_blocks:
                        continue
                    elif block.blockid == "minecraft:red_concrete":  # vrm 0
                        vrm = 2
                        if get_cell_value(vrm, row, col) > 0:
                            vrm0 += 1
                    elif block.blockid == "minecraft:blue_concrete":  # vrm 1
                        vrm = 3
                        if get_cell_value(vrm, row, col) > 0:
                            vrm1 += 1
                    elif block.blockid == "minecraft:cyan_concrete":  # vrm 2
                        vrm = 4
                        if get_cell_value(vrm, row, col) > 0:
                            vrm2 += 1
                    elif block.blockid == "minecraft:light_blue_concrete":  # vrm 3
                        vrm = 5
                        if get_cell_value(vrm, row, col) > 0:
                            vrm3 += 1
                    # calculating average stem, shroomlight and wart block values
                    avg_stems += get_cell_value(0, row, col)
                    avg_shroomlights += get_cell_value(1, row, col)
                    avg_wart_blocks += get_cell_value(vrm, row, col)

    stem_E = avg_stems / const.AVG_STEMS
    shroomlight_E = avg_shroomlights / const.AVG_SHROOMS
    wart_block_E = avg_wart_blocks / const.AVG_WARTS
    # wart blocks max doesn't take into account vrm and the actual max warts including VRM is around 82 but that's infeasible in reality

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")

    return avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E, vrm0, vrm1, vrm2, vrm3

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