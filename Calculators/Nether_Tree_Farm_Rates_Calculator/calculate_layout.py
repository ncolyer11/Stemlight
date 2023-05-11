"""
a helper function that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a
given nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to
pre-calculated heatmaps in a .xlsx file to work out the average stems, shroomlights and wart blocks harvested per cycle
for that nether tree farm layout
"""

# if the below import function is underlined in red run `pip install litemapy`
from litemapy import Schematic
import time
# importing heatmap data array
from Assets import heatmap_data


# taking file input from user and checking to see if the path and schematic size is valid
def schematic_to_efficiency(path, hat_cycles, trunk_cycles):
    # to fix empty input bug
    if path == '':
        path = './Assets/empty_layout.litematic'
    schem = Schematic.load(path)
    reg = list(schem.regions.values())[0]

    start_time = time.time()
    # skipping unnecessary calculations if layout schematic is empty
    if schem == 'empty_layout.litematic':
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("\nElapsed time:", elapsed_time, "seconds")
        return 0, 0, 0, 0, 0, 0

    # function for accessing a single element/cell in the above array
    def get_cell_value(sheet_name2, row_number, column_number):
        return heatmap_data.heatmap_array[sheet_name2][row_number][column_number]

    # function that computes the instantaneous value of the avg stems and shroomlights of the layout
    def stems_and_shrooms(average_stems, average_shroomlights, row2, col2, hat_cycles2, trunk_cycles2):
        average_stems += comp_probability(get_cell_value(0, row2, col2), trunk_cycles2)  # 0: stem heatmap
        average_shroomlights += comp_probability(get_cell_value(1, row2, col2), hat_cycles2)  # 1: shroomlight heatmap
        return average_stems, average_shroomlights

    # function that calculates the complimentary probability of an event
    def comp_probability(success_chance, attempts):
        return 1 - (1 - success_chance) ** attempts

    # initialising variables
    Xrange, Yrange, Zrange = reg.xrange(), reg.yrange(), reg.zrange()
    avg_shroomlights, avg_wart_blocks, avg_stems = 0, 0, 0
    valid_encoding_blocks = {'minecraft:red_concrete', 'minecraft:blue_concrete', 'minecraft:cyan_concrete',
                             'minecraft:light_blue_concrete'}

    for y in Yrange:
        for x in Xrange:
            for z in Zrange:
                block = reg.getblock(x, y, z)
                X, Y, Z = x, y, z
                if min(Xrange) < 0:
                    X += 6
                if min(Yrange) < 0:
                    Y += 26
                if min(Zrange) < 0:
                    Z += 6

                # 3D data is stored in 'slices' on a 2D spreadsheet, hence some math is needed to convert between them
                col = X + (7 * Z)
                row = 26 - Y

                # setting vrm value
                if block.blockid not in valid_encoding_blocks:
                    continue
                elif block.blockid == "minecraft:red_concrete":  # vrm 0
                    vrm = 2
                elif block.blockid == "minecraft:blue_concrete":  # vrm 1
                    vrm = 3
                elif block.blockid == "minecraft:cyan_concrete":  # vrm 2
                    vrm = 4
                elif block.blockid == "minecraft:light_blue_concrete":  # vrm 3
                    vrm = 5

                # calculating stems and shroomlight values
                avg_stems, avg_shroomlights = stems_and_shrooms(avg_stems, avg_shroomlights, row, col,
                                                                hat_cycles, trunk_cycles)
                # calculating wart block values
                if X == 0 and Z == 0:
                    avg_wart_blocks += comp_probability(get_cell_value(vrm, row, col), trunk_cycles)
                else:
                    avg_wart_blocks += comp_probability(get_cell_value(vrm, row, col), hat_cycles)

    # finding the efficiencies of the layout factoring in the varying cycles
    stem_E = (avg_stems / (221 / 24)) / trunk_cycles
    shroomlight_E = (avg_shroomlights / 2.03192455026454) / hat_cycles
    wart_block_E = (avg_wart_blocks / 63.0252319962964 ** 2) * (62.045721996296 / hat_cycles + 0.97951 / trunk_cycles)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print("\nElapsed time:", elapsed_time, "seconds")

    return avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E
