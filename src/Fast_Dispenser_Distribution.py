"""A minimal program that helps calculate the optimal position to place
n dispensers on a custom size grid of nylium as fast as possible"""

import numpy as np
import src.Assets.constants as const

# Selection cache
selection_cache = np.array([
    [0.6535605838853813, 0.4997510328685407, 0.28798973593014715],
    [0.4997510328685407, 0.3660553272880777, 0.20149313967509574],
    [0.28798973593014715, 0.20149313967509574, 0.10577931226910778],
])

def fast_calculate_dist(length, width, disp_coords):
    """Calculate the distribution of foliage for a given set of dispenser offsets fast"""
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))
    x, y = np.ogrid[:width, :length]
    bm_for_prod = 0
    for (disp_x, disp_y) in disp_coords:
        x1 = np.abs(x - disp_x).astype(int)
        y1 = np.abs(y - disp_y).astype(int)
        
        sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                              selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
        disp_chance = (1 - foliage_grid[disp_x, disp_y])

        bm_for_prod += disp_chance
        foliage_grid += (1 - foliage_grid) * disp_chance * sel_chance
    
    total_folige = np.sum(foliage_grid)
    compost = (8 / 9 * np.sum(foliage_grid)) / const.FOLIAGE_PER_BM
    return total_folige / 9, bm_for_prod - compost

if __name__ == "__main__":
    print(fast_calculate_dist(5, 5, [[2,2], [1,3], [3,2]]))

