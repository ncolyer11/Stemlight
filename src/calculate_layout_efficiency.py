"""
A helper function that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a
given nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to
pre-calculated heatmaps in a python array to work out the average stems, shroomlights and wart blocks harvested per
cycle for that nether tree farm layout
- made by ncolyer
for more info on how this & the heatmaps were made visit the huge fungi huggers discord: https://discord.gg/EKKkyfcPPV
"""

from litemapy import Schematic
import time

# importing heatmap data array
from src.Assets import heatmap_data, constants as const


def schematic_to_values(path):
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
    # wart blocks max doesn't take into account vrm and the actual max warts including VRM still hasn't been found
    # well at least the max feasible with vrm as if you can predict the optimal vrm locations for a huge fungi before it
    # grows you'd get ~99 wart blocks per fungus, but this isn't possible without rng manipulation

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nElapsed time: {elapsed_time} seconds")

    return avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E, vrm0, vrm1, vrm2, vrm3
