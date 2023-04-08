"""
A program that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a given
nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to pre-calculated
heatmaps in a .xlsx file to work out the average stems, shroomlights and wart blocks harvested per cycle for that
nether tree farm layout
- made by ncolyer
for more info on how this & the heatmaps were made visit the huge fungi huggers discord: https://discord.gg/EKKkyfcPPV
"""
# if the below import function is underlined in red run `pip install litemapy`
from litemapy import Schematic
import tkinter as tk
from tkinter import filedialog
import time
# importing heatmap data array
import heatmap_data

# create hidden root window
root = tk.Tk()
root.withdraw()

print("\n"
      "\t\t╔════════════════════════════════════════════════════╗\n"
      "\t\t  NOTE: Make sure your litematic selection measures\n"
      "\t\t  7x27x7 and the base of the selection is centred on\n"
      "\t\t        the block directly above the nylium\n"
      "\t\t╚════════════════════════════════════════════════════╝\n")

# taking file input from user and checking to see if the schematic size is valid
schem = Schematic.load(filedialog.askopenfilename())
reg = list(schem.regions.values())[0]
if len(reg.xrange()) == 7 and len(reg.yrange()) == 27 and len(reg.zrange()) == 7:
    print("\nSchematic loaded succesfully :)\n")
else:
    print("\nSizeError: Ensure the volume of your schematic measures 7x27x7.\n")

start_time = time.time()

# destroy root window
root.destroy()


# function for accessing a single value/cell in the above array
def get_cell_value(sheet_name2, row_number, column_number):
    return heatmap_data.heatmap_array[sheet_name2][row_number][column_number]


# function that computes the instantaneous value of the avg stems and shroomlights of the layout
def stems_and_shrooms(average_stems, average_shroomlights, row2, col2):
    inst_stems = get_cell_value(0, row2, col2)
    inst_shrooms = get_cell_value(1, row2, col2)
    average_stems += inst_stems  # 0: stem heatmap
    average_shroomlights += inst_shrooms  # 1: shroomlight heatmap
    print(f"\t• Stems = {inst_stems}\n"
          f"\t• Shroomlights = {inst_shrooms}")
    return average_stems, average_shroomlights


# function that returns the upper and lower bounds of an array, as an array
def make_bound_array(list2):
    return [min(list2), max(list2)]


# initialising values
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

            if block.blockid != "minecraft:air":
                # 3D data is stored in a excel spreadsheet format in a 3D array,
                # hence some math is needed to convert between them
                col = X + (7 * Z)
                row = 26 - Y
                print(f"At block ({X - 1}, {Y}, {Z - 1}):")
                if block.blockid not in valid_encoding_blocks:
                    print(f"\t• INVALID blockstate: {block.blockid[10:]}")
                    continue
                elif block.blockid == "minecraft:red_concrete":  # vrm 0
                    vrm = 2
                elif block.blockid == "minecraft:blue_concrete":  # vrm 1
                    vrm = 3
                elif block.blockid == "minecraft:cyan_concrete":  # vrm 2
                    vrm = 4
                elif block.blockid == "minecraft:light_blue_concrete":  # vrm 3
                    vrm = 5
                inst_warts = get_cell_value(vrm, row, col)
                avg_wart_blocks += inst_warts
                print(f"\t• VRM{vrm - 2} = {inst_warts}")

                # calculating stems and shroomlight values
                avg_stems, avg_shroomlights = stems_and_shrooms(avg_stems, avg_shroomlights, row, col)


stem_E = avg_stems / (221 / 24)
shroomlight_E = avg_shroomlights / 2.03192455026454
wart_block_E = avg_wart_blocks / 63.0252319962964 
# wart blocks max doesn't take into account vrm and the actual max warts including VRM still hasn't been found
# well at least the max feasible with vrm as if you can predict the optimal vrm locations for a huge fungi before it
# grows you'd get ~99 wart blocks per fungus, but this isn't possible without rng manipulation

print(f"\n╔════════════════════════════════════════════════════════════════════════════╗\n"
      f"   Avg blocks harvested per fungus:\n"
      f"\t   • Stems: {avg_stems} @{stem_E}E\n"
      f"\t   • Shroomlights: {avg_shroomlights} @{shroomlight_E}E\n"
      f"\t   • Wart Blocks: {avg_wart_blocks} @{wart_block_E}E\n"
      f"   Within the selection: X: {make_bound_array(list(Xrange))} Y: {make_bound_array(list(Yrange))} Z:"
      f" {make_bound_array(list(Zrange))}"
      f"\n╚════════════════════════════════════════════════════════════════════════════╝ ")

end_time = time.time()
elapsed_time = end_time - start_time
print("\nElapsed time:", elapsed_time, "seconds")
