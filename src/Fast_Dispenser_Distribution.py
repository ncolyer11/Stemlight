"""A minimal program that helps calculate the optimal position to place
n dispensers on a custom size grid of nylium as fast as possible"""

import numpy as np

from src.Assets.constants import *
from src.Assets.heatmap_data import heatmap_array_xyz

# Selection cache
selection_cache = np.array([
    [0.6535605838853813, 0.4997510328685407, 0.28798973593014715],
    [0.4997510328685407, 0.3660553272880777, 0.20149313967509574],
    [0.28798973593014715, 0.20149313967509574, 0.10577931226910778],
])

# The following functions are designed to have little to no looped function calls,
# resulting in some repetitive code

# If you've ever done assembly coding, you'd know how expensive function calls are

def fast_calc_fung_dist(length, width, nylium_type, disp_coords, cycles, blocked_blocks):
    """Calculate the distribution of foliage for a given set of dispenser offsets fast"""
    if nylium_type == WARPED:
        return warped_calc_fung_dist(length, width, disp_coords, cycles, blocked_blocks)
    
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((length, width))
    row, col = np.ogrid[:length, :width]

    bm_for_prod = 0.0
    for _ in range(cycles):
        for disp in disp_coords:
            disp_row, disp_col = disp.row, disp.col
            
            row1 = np.abs(row - disp_row).astype(int)
            col1 = np.abs(col - disp_col).astype(int)
            
            sel_chance = np.where((row1 > 2) | (col1 > 2), 0,
                                selection_cache[np.minimum(row1, 2), np.minimum(col1, 2)])
            for row2, col2 in blocked_blocks:
                sel_chance[row2, col2] = 0

            disp_chance = (1 - foliage_grid[disp_row, disp_col])

            bm_for_prod += disp_chance
            # Again, don't double multiply the air chance above a selected dispenser
            foliage_grid += (1 - foliage_grid) * np.where(row1 + col1 == 0, 1, disp_chance) \
                            * sel_chance
    
        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            if disp.cleared == CLEARED:
                foliage_grid[disp.row, disp.col] = 0


    total_folige = np.sum(foliage_grid)
    compost = (8 / 9 * np.sum(foliage_grid)) / FOLIAGE_PER_BM
    return total_folige / 9, bm_for_prod - compost

def warped_calc_fung_dist(length, width, disp_coords, cycles, blocked_blocks):
    """Calculate the distribution of foliage for warped separately to crimson as it's slower"""
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((length, width))

    # 2D array for storing distribution of desired fungus
    des_fungi_grid = np.zeros((length, width))
    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0
    # Keep track of sprouts to deduct later from foliage compost total
    sprouts_grid = np.zeros((length, width))
    row, col = np.ogrid[:length, :width]
    for _ in range(cycles):
        for disp in disp_coords:
            disp_row, disp_col = disp.row, disp.col

            row1 = np.abs(row - disp_row).astype(int)
            col1 = np.abs(col - disp_col).astype(int)
            sel_chance = np.where((row1 > 2) | (col1 > 2), 0,
                                selection_cache[np.minimum(row1, 2), np.minimum(col1, 2)])
            for row2, col2 in blocked_blocks:
                sel_chance[row2, col2] = 0
            
            disp_chance = (1 - foliage_grid[disp_row, disp_col])
            bm_for_prod += disp_chance
            # Again, again, don't double multiply the air chance above a selected dispenser
            foliage_chance = sel_chance * np.where(row1 + col1 == 0, 1, disp_chance)

            des_fungi_grid += (1 - foliage_grid) * foliage_chance * WARP_FUNG_CHANCE
            
            foliage_grid += (1 - foliage_grid) * foliage_chance
            
            # As it's warped nylium, generate sprouts
            sprouts_chance = (1 - foliage_grid) * foliage_chance
            foliage_grid += sprouts_chance
            sprouts_grid += sprouts_chance

        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            if disp.cleared == CLEARED:
                foliage_grid[disp.row, disp.col] = 0
                des_fungi_grid[disp.row, disp.col] = 0
                sprouts_grid[disp.row, disp.col] = 0
    
    total_des_fungi = np.sum(des_fungi_grid)
    compost = (np.sum(foliage_grid) - total_des_fungi - np.sum(sprouts_grid)) / FOLIAGE_PER_BM
    return total_des_fungi, bm_for_prod - compost

def fast_calc_hf_dist(length, width, nylium_type, disp_coords, cycles, blocked_blocks):
    """Doesn't take into account stem occlusion (for speed), but should still optimise fine"""
    p_length = length
    p_width = width
    if nylium_type == WARPED:
        return warped_calc_hf_dist(p_length, p_width, disp_coords, cycles, blocked_blocks)
    
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((p_length, p_width))
    row, col = np.ogrid[:p_length, :p_width]
    bm_for_prod = 0.0
    for _ in range(cycles):
        for disp in disp_coords:
            disp_row, disp_col = disp.row, disp.col
            
            row1 = np.abs(row - disp_row).astype(int)
            col1 = np.abs(col - disp_col).astype(int)
            
            sel_chance = np.where((row1 > 2) | (col1 > 2), 0,
                                selection_cache[np.minimum(row1, 2), np.minimum(col1, 2)])
            for row2, col2 in blocked_blocks:
                sel_chance[row2, col2] = 0
            
            disp_chance = (1 - foliage_grid[disp_row, disp_col])
            bm_for_prod += disp_chance
            foliage_grid += (1 - foliage_grid) * np.where(row1 + col1 == 0, 1, disp_chance) \
                            * sel_chance

        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            # Clear foliage only on top of cleared dispensers except
            if disp.cleared == CLEARED:
                foliage_grid[disp.row, disp.col] = 0
    
    compost_from_foliage = (8 / 9 * np.sum(foliage_grid)) / FOLIAGE_PER_BM
    bm_for_prod -= compost_from_foliage

    hf_width = NT_MAX_RAD + p_width + NT_MAX_RAD
    hf_length = NT_MAX_RAD + p_length + NT_MAX_RAD
    hf_grid = np.zeros((NT_MAX_HT, hf_width, hf_length))

    # Create coordinate grids
    nylium_x, nylium_z = np.meshgrid(np.arange(p_width), np.arange(p_length))
    y, z, x = np.meshgrid(np.arange(NT_MAX_HT), np.arange(NT_MAX_WD), np.arange(NT_MAX_WD))

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
    foliage_grid = np.zeros((p_length, p_width))

    # 2D array for storing distribution of desired fungus
    des_fungi_grid = np.zeros((p_length, p_width))
    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0
    # Keep track of sprouts to deduct later from foliage compost total
    sprouts_grid = np.zeros((p_length, p_width))

    row, col = np.ogrid[:p_length, :p_width]
    for _ in range(cycles):
        for disp in disp_coords:
            disp_row, disp_col = disp.row, disp.col

            row1 = np.abs(row - disp_row).astype(int)
            col1 = np.abs(col - disp_col).astype(int)
            sel_chance = np.where((row1 > 2) | (col1 > 2), 0,
                                selection_cache[np.minimum(row1, 2), np.minimum(col1, 2)])
            for row2, col2 in blocked_blocks:
                sel_chance[row2, col2] = 0

            disp_chance = (1 - foliage_grid[disp_row, disp_col])
            bm_for_prod += disp_chance
            foliage_chance = sel_chance * np.where(row1 + col1 == 0, 1, disp_chance)

            des_fungi_grid += (1 - foliage_grid) * foliage_chance * WARP_FUNG_CHANCE
            
            foliage_grid += (1 - foliage_grid) * foliage_chance
            
            # As it's warped nylium, generate sprouts
            sprouts_chance = (1 - foliage_grid) * foliage_chance
            foliage_grid += sprouts_chance
            sprouts_grid += sprouts_chance

        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in disp_coords:
            # Clear foliage only on top of cleared dispensers
            if disp.cleared == CLEARED:
                foliage_grid[disp.row, disp.col] = 0
                des_fungi_grid[disp.row, disp.col] = 0
                sprouts_grid[disp.row, disp.col] = 0
   
    total_des_fungi = np.sum(des_fungi_grid)
    compost = (np.sum(foliage_grid) - total_des_fungi - np.sum(sprouts_grid)) / FOLIAGE_PER_BM

    width = NT_MAX_RAD + p_width + NT_MAX_RAD
    length = NT_MAX_RAD + p_length + NT_MAX_RAD
    hf_grid = np.zeros((NT_MAX_HT, width, length))

    # Create coordinate grids
    nylium_x, nylium_z = np.meshgrid(np.arange(p_width), np.arange(p_length))
    y, z, x = np.meshgrid(np.arange(NT_MAX_HT), np.arange(NT_MAX_WD), np.arange(NT_MAX_WD))

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
