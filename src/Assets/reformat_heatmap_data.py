import numpy as np
import src.Assets.constants as const
from src.Assets.helpers import get_cell_value
from src.Assets import heatmap_data

def compress_heatmap_data():
    # Initialize a compressed heatmap array
    compressed_heatmap_array = np.zeros((len(const.BLOCK_TYPES), const.NT_MAX_WD, const.NT_MAX_WD))

    # Iterate through each block type
    for b in range(len(const.BLOCK_TYPES)):
        # Iterate through each x, z position in the 7x7 grid
        for x in range(const.NT_MAX_WD):
            for z in range(const.NT_MAX_WD):
                # Sum values for the (x, z) position across all y slices
                sum_value = 0
                for y in range(const.NT_MAX_HT):
                    # Calculate the row and column in the spreadsheet
                    row = y
                    col = x + (z * const.NT_MAX_WD)
                    sum_value += get_cell_value(b, row, col)
                compressed_heatmap_array[b][z][x] = sum_value

    # Write the compressed_heatmap_array to a Python file
    with open('compressed_heatmap_array.py', 'w') as file:
        file.write('import numpy as np\n\n')
        file.write('# Compressed heatmap array\n')
        file.write('compressed_heatmap_array = np.array([\n')
        for b in range(len(const.BLOCK_TYPES)):
            file.write('    [\n')
            for z in range(const.NT_MAX_WD):
                file.write('        [')
                file.write(', '.join(f'{value:.7e}' for value in compressed_heatmap_array[b][z]))
                file.write(']')
                if z < const.NT_MAX_WD - 1:
                    file.write(',\n')
                else:
                    file.write('\n')
            if b < len(const.BLOCK_TYPES) - 1:
                file.write('    ],\n\n')
            else:
                file.write('    ]\n')
        file.write('])\n\n')

    # Print sums of each subarray
    for b, block_type in enumerate(const.BLOCK_TYPES):
        subarray_sum = np.sum(compressed_heatmap_array[b])
        print(f"Sum of {block_type}: {subarray_sum:.7e}")

def make_excel_cartesian():
    # Initialize a compressed heatmap array
    compressed_heatmap_array = np.zeros((len(const.BLOCK_TYPES) + 3, const.NT_MAX_HT, const.NT_MAX_WD, const.NT_MAX_WD))

    # Helper function to get cell value from the heatmap array
    def get_cell_value(sheet_name, row_number, column_number):
        return heatmap_data.heatmap_array[sheet_name][row_number][column_number]

    # Iterate through each block type
    for b in range(len(const.BLOCK_TYPES) + 3):
        # Iterate through each x, z position in the 7x7 grid
        for x in range(const.NT_MAX_WD):
            for z in range(const.NT_MAX_WD):
                # Iterate through each y position
                for y in range(const.NT_MAX_HT):
                    # Calculate the row and column in the spreadsheet
                    row = y
                    col = x + (z * const.NT_MAX_WD)
                    compressed_heatmap_array[b][y][z][x] = get_cell_value(b, row, col)

    # Write the compressed_heatmap_array to a Python file
    with open('cartesian_heatmap_array.py', 'w') as file:
        file.write('import numpy as np\n\n')
        file.write('# Compressed heatmap array\n')
        file.write('heatmap_array_xyz = np.array([\n')
        for b in range(len(const.BLOCK_TYPES) + 3):
            file.write('    [\n')
            for y in range(const.NT_MAX_HT):
                file.write('        [\n')
                for z in range(const.NT_MAX_WD):
                    file.write('            [')
                    file.write(', '.join(f'{compressed_heatmap_array[b][y][z][x]:.7e}' for x in range(const.NT_MAX_WD)))
                    file.write(']')
                    if z < const.NT_MAX_WD - 1:
                        file.write(',\n')
                    else:
                        file.write('\n')
                if y < const.NT_MAX_HT - 1:
                    file.write('        ],\n')
                else:
                    file.write('        ]\n')
            if b < len(const.BLOCK_TYPES) + 2:
                file.write(f'    ],\n    # Block type {b}:\n')
            else:
                file.write('    ]\n')
        file.write('])\n\n')
