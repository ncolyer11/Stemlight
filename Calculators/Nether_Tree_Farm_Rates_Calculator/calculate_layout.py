"""
program that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a given
nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to pre-calculated
heatmaps in a .xlsx file to work out the average stems, shroomlights and wart blocks harvested per cycle for that
nether tree farm layout
"""

# if the below import functions are underlined in red run `pip install litemapy` and `pip install openpyxl`
from litemapy import Schematic
import openpyxl


# taking file input from user and checking to see if the path and schematic size is valid
def schematic_to_efficiency(path):
    schem = Schematic.load(f"{path}")
    reg = list(schem.regions.values())[0]

    workbook = openpyxl.load_workbook('heatmaps.xlsx')
    cell_values = {}

    # opening the heatmap excel spreadsheet once and writing all the values to an array
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        for row in sheet.iter_rows():
            for cell in row:
                cell_values[(sheet_name, cell.row, cell.column)] = cell.value

    # function for accessing a single value/cell in the above array
    def get_cell_value(sheet_name2, row_number, column_number):
        return cell_values[(sheet_name2, row_number, column_number)]

    # function that computes the instantaneous value of the avg stems and shroomlights of the layout
    def stems_and_shrooms(average_stems, average_shroomlights, row2, col2):
        average_stems += get_cell_value('stems', row2, col2)
        average_shroomlights += get_cell_value('shroomlights', row2, col2)
        # print(f"\t• Stems = {get_cell_value('stems', row2, col2)}\n"
        # f"\t• Shroomlights = {get_cell_value('shroomlights', row2, col2)}")
        return average_stems, average_shroomlights

    # initialising variables
    Xrange, Yrange, Zrange = reg.xrange(), reg.yrange(), reg.zrange()
    avg_shroomlights, avg_wart_blocks, avg_stems = 0, 0, 0

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
                if block.blockid == "minecraft:air":
                    continue
                # print(f"\t• INVALID blockstate: {block.blockid[10:]}")
                col = X + (7 * Z) + 1
                row = 27 - Y
                # print(f"At block ({X}, {Y}, {Z}):")
                if block.blockid == "minecraft:red_concrete":
                    avg_stems, avg_shroomlights = stems_and_shrooms(avg_stems, avg_shroomlights, row, col)
                    avg_wart_blocks += get_cell_value('vrm0', row, col)
                    # print(f"\t• VRM0 = {get_cell_value('vrm0', row, col)}")
                elif block.blockid == "minecraft:blue_concrete":
                    avg_stems, avg_shroomlights = stems_and_shrooms(avg_stems, avg_shroomlights, row, col)
                    avg_wart_blocks += get_cell_value('vrm1', row, col)
                    # print(f"\t• VRM1 = {get_cell_value('vrm1', row, col)}")
                elif block.blockid == "minecraft:cyan_concrete":
                    avg_stems, avg_shroomlights = stems_and_shrooms(avg_stems, avg_shroomlights, row, col)
                    avg_wart_blocks += get_cell_value('vrm2', row, col)
                    # print(f"\t• VRM2 = {get_cell_value('vrm2', row, col)}")
                elif block.blockid == "minecraft:light_blue_concrete":
                    avg_stems, avg_shroomlights = stems_and_shrooms(avg_stems, avg_shroomlights, row, col)
                    avg_wart_blocks += get_cell_value('vrm3', row, col)
                    # print(f"\t• VRM3 = {get_cell_value('vrm3', row, col)}")

    stem_E = 24 * avg_stems / 221
    shroomlight_E = avg_shroomlights / 2.03192455026454
    wart_block_E = avg_wart_blocks / 63.0252319962964

    return avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E
