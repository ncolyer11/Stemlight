"""produces a heatmap for fungi grown on a custom sized nylium platform"""

import xlsxwriter
import time

from src.Assets import heatmap_data, constants as const

def start(root):
    DP_VAL = 5

    def get_cell_value(sheet_name, row_number, column_number):
        return heatmap_data.heatmap_array[sheet_name][row_number][column_number]

    # get input from user
    width = int(input("Enter Width of Nylium Grid: "))
    heatmap_width = const.NT_MAX_RAD + width + const.NT_MAX_RAD

    length = int(input("Enter Length of Nylium Grid: "))
    heatmap_length = const.NT_MAX_RAD + length + const.NT_MAX_RAD

    dispensers = int(input("Enter Amount of Dispensers: "))

    # start tracking time
    start_time = time.time()

    custom_heatmap_array = [[[[0 for _ in range(const.NT_MAX_HT)] for _ in range(heatmap_width)] for _ in range(heatmap_length)] for _ in range(const.BLOCK_TYPES)]

    coordinates = []
    for i in range(dispensers):
        while True:
            x = int(input(f'Enter x-Offset from NW corner for dispenser {i + 1}: '))
            y = int(input(f'Enter y-Offset from NW corner for dispenser {i + 1}: '))
            if 0 <= x < width and 0 <= y < length:
                coordinates.append((x, y))
                break
            else:
                print(f'Error: The offset values must be within the bounds of the {width}x{length} grid.')

    # Create 2D array of given size and initialize all elements to 0
    nyliumGrid = [[0 for i in range(length)] for j in range(width)]
    def selection_chance(x1, y1):
        x2 = const.FUNG_SPREAD_RAD - abs(x1)
        y2 = const.FUNG_SPREAD_RAD - abs(y1)
        P_block = x2 * y2 / (const.FUNG_SPREAD_RAD ** 4)
        P_block = 0 if x2 < 0 or y2 < 0 else P_block
        P = 0
        for k in range(1, const.FUNG_SPREAD_RAD ** 2 + 1):
            P += (1 - P_block) ** (const.FUNG_SPREAD_RAD ** 2 - k)
        return P * P_block * const.CRMS_FUNG_CHANCE  # 11/99 for crimson and 13/100 for warped


    for i in range(dispensers):
        # chance of dispenser being able to fire from lack of foliage above it
        C = (1 - nyliumGrid[coordinates[i][0]][coordinates[i][1]])
        for x in range(width):
            for y in range(length):
                S = selection_chance(x - coordinates[i][0], y - coordinates[i][1])
                B = nyliumGrid[x][y] * C * S
                nyliumGrid[x][y] = round(nyliumGrid[x][y] + C * S - B, DP_VAL)

    # writing weighted data to custom heatmaps
    outSheet = []
    outWorkbook = xlsxwriter.Workbook(r"fungi_weighted_heatmap.xlsx")

    blocks = 0
    for block_type in range(const.BLOCK_TYPES):  # 0 = stems, 1 = shrooms, 2 = vrm0/warts
        outSheet.append(outWorkbook.add_worksheet(f"{block_type}"))
        for nylium_x in range(width):
            for nylium_z in range(length):
                heatmap_weighting = nyliumGrid[nylium_x][nylium_z]
                for y in range(const.NT_MAX_HT):
                    for z in range(const.NT_MAX_WD):
                        for x in range(const.NT_MAX_WD):
                            col = x + (const.NT_MAX_WD * z)
                            row = const.NT_MAX_HT - 1 - y
                            weighted_chance = heatmap_weighting * get_cell_value(block_type, row, col)
                            # print(f"type: {block_type}, x: {nylium_x + x}, z: {nylium_z + z}, y: {y}, weight: {heatmap_weighting}")
                            custom_heatmap_array[block_type][nylium_z + z][nylium_x + x][y] += weighted_chance

        for y in range(const.NT_MAX_HT):
            for z in range(heatmap_width):
                for x in range(heatmap_length):
                    col = x + (heatmap_width * z)
                    row = const.NT_MAX_HT - 1 - y
                    heatmap_data_point = custom_heatmap_array[block_type][x][z][y]
                    outSheet[block_type].write(row, col, heatmap_data_point)
                    blocks += 1
                    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Heatmap data calculated and output to excel file in {elapsed_time} seconds")
    outWorkbook.close()
