"""A minimal program that helps calculate the optimal position to place
n dispensers on a custom size grid of nylium as fast as possible"""

import numpy as np
import src.Assets.constants as const
from src.Assets.heatmap_data import heatmap_array_xyz

WARPED = 0
CRIMSON = 1

# Selection cache
selection_cache = np.array([
    [0.6535605838853813, 0.4997510328685407, 0.28798973593014715],
    [0.4997510328685407, 0.3660553272880777, 0.20149313967509574],
    [0.28798973593014715, 0.20149313967509574, 0.10577931226910778],
])

# The following functions are designed to have little to no looped function calls,
# resulting in some repetitive code

def fast_calc_fung_dist(length, width, fungus_type, disp_coords, cycles, blocked_blocks):
    """Calculate the distribution of foliage for a given set of dispenser offsets fast"""
    if fungus_type == WARPED:
        return warped_calc_fung_dist(length, width, disp_coords, cycles, blocked_blocks)
    
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))
    x, y = np.ogrid[:width, :length]

    bm_for_prod = 0.0
    for _ in range(cycles):
        for (disp_x, disp_y, _) in disp_coords:
            # Dispensers placed on blocked blocks don't do shit bud
            if (disp_x, disp_y) in blocked_blocks:
                continue
            x1 = np.abs(x - disp_x).astype(int)
            y1 = np.abs(y - disp_y).astype(int)
            
            sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                                selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
            for x2, y2 in blocked_blocks:
                sel_chance[x2, y2] = 0

            disp_chance = (1 - foliage_grid[disp_x, disp_y])

            bm_for_prod += disp_chance
            foliage_grid += (1 - foliage_grid) * disp_chance * sel_chance
    
        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            # Clear foliage only on top of cleared dispensers except
            if disp[2] == 0:
                continue
            disp_x, disp_y, _ = disp
            foliage_grid[disp_x, disp_y] = 0


    total_folige = np.sum(foliage_grid)
    compost = (8 / 9 * np.sum(foliage_grid)) / const.FOLIAGE_PER_BM
    return total_folige / 9, bm_for_prod - compost

def warped_calc_fung_dist(length, width, disp_coords, cycles, blocked_blocks):
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
    for _ in range(cycles):
        for (disp_x, disp_y, _) in disp_coords:
            if (disp_x, disp_y) in blocked_blocks:
                continue
            x1 = np.abs(x - disp_x).astype(int)
            y1 = np.abs(y - disp_y).astype(int)
            sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                                selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
            
            for x2, y2 in blocked_blocks:
                sel_chance[x2, y2] = 0
            
            disp_chance = (1 - foliage_grid[disp_x, disp_y])
            bm_for_prod += disp_chance
            foliage_chance = sel_chance * disp_chance

            des_fungi_grid += (1 - foliage_grid) * foliage_chance * const.WARP_FUNG_CHANCE
            
            foliage_grid += (1 - foliage_grid) * foliage_chance
            
            # As it's warped nylium, generate sprouts
            sprouts_chance = (1 - foliage_grid) * foliage_chance
            foliage_grid += sprouts_chance
            sprouts_total += sprouts_chance

        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            # Clear foliage only on top of cleared dispensers except
            if disp[2] == 0:
                continue
            disp_x, disp_y, _ = disp
            foliage_grid[disp_x, disp_y] = 0
            des_fungi_grid[disp_x, disp_y] = 0
    
    total_des_fungi = np.sum(des_fungi_grid)
    compost = (np.sum(foliage_grid) - total_des_fungi - np.sum(sprouts_total)) / const.FOLIAGE_PER_BM
    return total_des_fungi, bm_for_prod - compost

def fast_calc_hf_dist(p_length, p_width, fungus_type, disp_coords, cycles, blocked_blocks):
    if fungus_type == WARPED:
        return warped_calc_hf_dist(p_length, p_width, disp_coords, cycles, blocked_blocks)
    
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((p_width, p_length))
    x, y = np.ogrid[:p_width, :p_length]
    bm_for_prod = 0.0
    for _ in range(cycles):
        for (disp_x, disp_y, _) in disp_coords:
            if (disp_x, disp_y) in blocked_blocks:
                continue
            x1 = np.abs(x - disp_x).astype(int)
            y1 = np.abs(y - disp_y).astype(int)
            
            sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                                selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
            for x2, y2 in blocked_blocks:
                sel_chance[x2, y2] = 0
            disp_chance = (1 - foliage_grid[disp_x, disp_y])

            bm_for_prod += disp_chance
            foliage_grid += (1 - foliage_grid) * disp_chance * sel_chance

        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            # Clear foliage only on top of cleared dispensers except
            if disp[2] == 0:
                continue
            disp_x, disp_y, _ = disp
            foliage_grid[disp_x, disp_y] = 0
    
    compost_from_foliage = (8 / 9 * np.sum(foliage_grid)) / const.FOLIAGE_PER_BM
    bm_for_prod -= compost_from_foliage

    width = const.NT_MAX_RAD + p_width + const.NT_MAX_RAD
    length = const.NT_MAX_RAD + p_length + const.NT_MAX_RAD
    hf_grid = np.zeros((const.NT_MAX_HT, width, length))

    # Create coordinate grids
    nylium_x, nylium_z = np.meshgrid(np.arange(p_width), np.arange(p_length))
    y, z, x = np.meshgrid(np.arange(const.NT_MAX_HT), np.arange(const.NT_MAX_WD), np.arange(const.NT_MAX_WD))

    # Calculate heatmap weighting
    heatmap_weighting = foliage_grid / 9

    # Iterate through each x,z coord in the nylium grid/platform 
    for nylium_x_idx, nylium_z_idx in np.ndindex(nylium_x.shape):
        nylium_x_curr = nylium_x[nylium_x_idx, nylium_z_idx]
        nylium_z_curr = nylium_z[nylium_x_idx, nylium_z_idx]
        heatmap_weighting_curr = heatmap_weighting[nylium_x_idx, nylium_z_idx]

        # Calculate weighted chance for all y,z,x coordinates
        weighted_chance = heatmap_weighting_curr * heatmap_array_xyz[2, y, z, x]

        # Update hf_grid for all y,z,x coordinates
        curr = hf_grid[y, nylium_z_curr + z, nylium_x_curr + x]
        hf_grid[y, nylium_z_curr + z, nylium_x_curr + x] += (1 - curr) * weighted_chance

    total_wb = np.sum(hf_grid)
    return total_wb, bm_for_prod

def warped_calc_hf_dist(p_length, p_width, disp_coords, cycles, blocked_blocks):
    """Calculate the distribution of foliage and wart blocks for warped separately to crimson"""
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((p_width, p_length))

    # 2D array for storing distribution of desired fungus
    des_fungi_grid = np.zeros((p_width, p_length))
    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0
    # Keep track of sprouts to deduct later from foliage compost total
    sprouts_total = 0.0

    x, y = np.ogrid[:p_width, :p_length]
    for _ in range(cycles):
        for (disp_x, disp_y) in disp_coords:
            if (disp_x, disp_y) in blocked_blocks:
                continue
            x1 = np.abs(x - disp_x).astype(int)
            y1 = np.abs(y - disp_y).astype(int)
            sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                                selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
            for x2, y2 in blocked_blocks:
                sel_chance[x2, y2] = 0

            disp_chance = (1 - foliage_grid[disp_x, disp_y])
            bm_for_prod += disp_chance
            foliage_chance = sel_chance * disp_chance

            des_fungi_grid += (1 - foliage_grid) * foliage_chance * const.WARP_FUNG_CHANCE
            
            foliage_grid += (1 - foliage_grid) * foliage_chance
            
            # As it's warped nylium, generate sprouts
            sprouts_chance = (1 - foliage_grid) * foliage_chance
            foliage_grid += sprouts_chance
            sprouts_total += sprouts_chance

        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            # Clear foliage only on top of cleared dispensers except
            if disp[2] == 0:
                continue
            disp_x, disp_y, _ = disp
            foliage_grid[disp_x, disp_y] = 0
            des_fungi_grid[disp_x, disp_y] = 0
            sprouts_total[disp_x, disp_y] = 0
   
    total_des_fungi = np.sum(des_fungi_grid)
    compost = (np.sum(foliage_grid) - total_des_fungi - np.sum(sprouts_total)) / const.FOLIAGE_PER_BM

    width = const.NT_MAX_RAD + p_width + const.NT_MAX_RAD
    length = const.NT_MAX_RAD + p_length + const.NT_MAX_RAD
    hf_grid = np.zeros((const.NT_MAX_HT, width, length))

    # Create coordinate grids
    nylium_x, nylium_z = np.meshgrid(np.arange(p_width), np.arange(p_length))
    y, z, x = np.meshgrid(np.arange(const.NT_MAX_HT), np.arange(const.NT_MAX_WD), np.arange(const.NT_MAX_WD))

    # Iterate through each x,z coord in the nylium grid/platform 
    for nylium_x_idx, nylium_z_idx in np.ndindex(nylium_x.shape):
        nylium_x_curr = nylium_x[nylium_x_idx, nylium_z_idx]
        nylium_z_curr = nylium_z[nylium_x_idx, nylium_z_idx]
        heatmap_weighting_curr = des_fungi_grid[nylium_x_idx, nylium_z_idx]

        # Calculate weighted chance for all y,z,x coordinates
        weighted_chance = heatmap_weighting_curr * heatmap_array_xyz[2, y, z, x]

        # Update hf_grid for all y,z,x coordinates
        curr = hf_grid[y, nylium_z_curr + z, nylium_x_curr + x]
        hf_grid[y, nylium_z_curr + z, nylium_x_curr + x] += (1 - curr) * weighted_chance

    total_wb = np.sum(hf_grid)
    return total_wb, bm_for_prod - compost

if __name__ == "__main__":
    # print(fast_calc_fung_dist(5, 5, [[2,2], [1,3], [3,2]]))
    fast_calc_hf_dist(5,5,1,[[2,2]])
