"""Produces a heatmap for fungi grown on a custom sized nylium platform"""

import xlsxwriter
import time

from src.Assets import heatmap_data, constants as const
import itertools
import numpy as np

def get_cell_value(sheet_name, row_number, column_number):
    """Return the value of the cell at the given row and column in the given sheet."""
    return heatmap_data.heatmap_array[sheet_name][row_number][column_number]

def export_custom_heatmaps(length, width, nyliumGrid):
    """Export the custom nether tree heatmap data, generated\n 
    from the dispenser placements, to an Excel file."""
    print(nyliumGrid)
    try:
        outSheet = []
        outWorkbook = xlsxwriter.Workbook(r"weighted_fungi_heatmap.xlsx")
        start_time = time.time()
        
        heatmap_length = const.NT_MAX_RAD + length + const.NT_MAX_RAD
        heatmap_width = const.NT_MAX_RAD + width + const.NT_MAX_RAD
        custom_heatmap_array = np.zeros((
            len(const.BLOCK_TYPES), 
            heatmap_length,
            heatmap_width,
            const.NT_MAX_HT
        ))
        for b, block_type in enumerate(const.BLOCK_TYPES):  # 0 = stems, 1 = shrooms, 2 = vrm0/warts
            outSheet.append(outWorkbook.add_worksheet(block_type))
            # Iterate through each x,z coord in the nylium grid/platform 
            for nylium_x, nylium_z in itertools.product(range(width), range(length)):
                heatmap_weighting = nyliumGrid[nylium_x][nylium_z]
                y_range, z_range, x_range = range(const.NT_MAX_HT), range(const.NT_MAX_WD), range(const.NT_MAX_WD)
                # Iterate through each x,y,z coord relative to the fungi
                for y, z, x in itertools.product(y_range, z_range, x_range):
                    col = x + (const.NT_MAX_WD * z)
                    row = const.NT_MAX_HT - 1 - y
                    weighted_chance = heatmap_weighting * get_cell_value(b, row, col)
                    custom_heatmap_array[b][nylium_z + z][nylium_x + x][y] += weighted_chance

            # Write data to Excel file for each block type
            y_range, z_range, x_range = range(const.NT_MAX_HT), range(heatmap_width), range(heatmap_length)
            for y, z, x in itertools.product(y_range, z_range, x_range):
                col = x + (heatmap_width * z)
                row = const.NT_MAX_HT - 1 - y
                heatmap_data_point = custom_heatmap_array[b][x][z][y]
                outSheet[b].write(row, col, heatmap_data_point)
                        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Heatmap data calculated and output to excel file in {elapsed_time} seconds")
        outWorkbook.close()
        return 0
    except Exception as e:
        print(f"Error occurred whilst exporting heatmaps: {e}")
        return e
