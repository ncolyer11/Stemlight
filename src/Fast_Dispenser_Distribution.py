"""A minimal program that helps calculate the optimal position to place
n dispensers on a custom size grid of nylium as fast as possible"""

import numpy as np
import src.Assets.constants as const

WARPED = 0
CRIMSON = 1

# Selection cache
selection_cache = np.array([
    [0.6535605838853813, 0.4997510328685407, 0.28798973593014715],
    [0.4997510328685407, 0.3660553272880777, 0.20149313967509574],
    [0.28798973593014715, 0.20149313967509574, 0.10577931226910778],
])

def fast_calculate_dist(length, width, fungus_type, disp_coords):
    """Calculate the distribution of foliage for a given set of dispenser offsets fast"""
    if fungus_type == WARPED:
        return warped_calculate_dist(length, width, disp_coords)
    
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))
    x, y = np.ogrid[:width, :length]
    bm_for_prod = 0.0
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

def warped_calculate_dist(length, width, disp_coords):
    """Calculate the distribution of foliage for warped separately to crimson as it's slower"""
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))

    # 2D array for storing distribution of desired fungus
    des_fungi_grid = np.zeros((width, length))
    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0
    # Keep track of sprouts to deduct later from foliage compost total
    sprouts_total = 0.0

    x, y = np.ogrid[:width, :length]
    for (disp_x, disp_y) in disp_coords:
        x1 = np.abs(x - disp_x).astype(int)
        y1 = np.abs(y - disp_y).astype(int)
        sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                              selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
        disp_chance = (1 - foliage_grid[disp_x, disp_y])
        bm_for_prod += disp_chance
        foliage_chance = sel_chance * disp_chance

        des_fungi_grid += (1 - foliage_grid) * foliage_chance * const.WARP_FUNG_CHANCE
        
        foliage_grid += (1 - foliage_grid) * foliage_chance
        
        # As it's warped nylium, generate sprouts
        sprouts_chance = (1 - foliage_grid) * foliage_chance
        foliage_grid += sprouts_chance
        sprouts_total += sprouts_chance
    
    total_des_fungi = np.sum(des_fungi_grid)
    compost = (np.sum(foliage_grid) - total_des_fungi - np.sum(sprouts_total)) / const.FOLIAGE_PER_BM
    return total_des_fungi, bm_for_prod - compost

if __name__ == "__main__":
    print(fast_calculate_dist(5, 5, [[2,2], [1,3], [3,2]]))
