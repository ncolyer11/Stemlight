import os
import sys
import tkinter as tk
import os
import sys
from litemapy import Schematic
import time

from src.Assets import heatmap_data, constants as const

from src.Assets.version import version

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
            pass  # If that also fails, do nothing

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