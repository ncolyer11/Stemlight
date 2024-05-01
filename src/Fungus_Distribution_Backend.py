"""A program that helps calculate the optimal position to place n dispensers on a custom size grid of nylium"""

import numpy as np

from src.Assets import constants as const

DP_VAL = 5
WARPED = 0
CRIMSON = 1


def selection_chance(x1, y1):
    """Calculates the probability of a block being selected for 
    foliage generation given its offset from a dispenser"""
    # Selection values derived from little formula cooked up on Desmos
    P = [
        0.10577931226910778, 0.20149313967509574,
        0.28798973593014715, 0.3660553272880777,
        0.4997510328685407, 0.6535605838853813
    ]
    # Integer equivalent weights (multiply by 81^9/[1,2,3,4,6,9])
    I = [
        15876907296999121, 15121519657190401,
        14408571461238171, 13735735211956921,
        12501658169617041, 10899548609196681
    ]
    # Foliage is centrally distributed around the dispenser
    selection_cache = np.array([
        [P[5], P[4], P[2]],
        [P[4], P[3], P[1]],
        [P[2], P[1], P[0]],
    ])
    # Normalising
    x1 = np.abs(x1).astype(int)
    y1 = np.abs(y1).astype(int)
    # Need to take min of x1 and y1 to avoid index out of bounds as numpy evaluates both branches
    return np.where((x1 > 2) | (y1 > 2), 0, selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])

def calculate_distribution(length, width, dispensers, disp_coords, fungi_weight, fungi):
    # 3D array for storing distribution of foliage for all dispensers
    disp_foliage_grids = np.zeros((dispensers, width, length))
    # 2D array for storing distribution of all the foliage
    total_foliage_grid = np.zeros((width, length))

    # 3D array for storing distribution of desired fungus for all dispensers
    disp_des_fungi_grids = np.zeros((dispensers, width, length))
    # 2D array for storing distribution of desired fungus
    total_des_fungi_grid = np.zeros((width, length))
    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0

    x, y = np.ogrid[:width, :length]
    for i in range(dispensers):
        foliage_chance, bm_for_prod = generate_foliage(disp_coords, total_foliage_grid, bm_for_prod, i, x, y)
        
        des_fungi_chance = foliage_chance * fungi_weight
        disp_des_fungi_grids[i] = (1 - total_foliage_grid) * des_fungi_chance
        total_des_fungi_grid += disp_des_fungi_grids[i]
        
        disp_foliage_grids[i] = (1 - total_foliage_grid) * foliage_chance
        total_foliage_grid += disp_foliage_grids[i]
        
        # If warped nylium, generate sprouts
        if fungi == WARPED:
            sprouts_chance = (1 - total_foliage_grid) * foliage_chance
            disp_foliage_grids[i] += sprouts_chance
            total_foliage_grid += sprouts_chance
            

    return total_foliage_grid, total_des_fungi_grid, bm_for_prod, \
        disp_foliage_grids, disp_des_fungi_grids

def generate_foliage(disp_coords, foliage_grid, bm_for_prod, i, x, y,):
    disp_x = disp_coords[i][0]
    disp_y = disp_coords[i][1]
    disp_bm_chance = 1 - foliage_grid[disp_x, disp_y]
    bm_for_prod += disp_bm_chance

    # P(foliage at x,y) = P(Air above dispensers) * P(x,y being selected)
    foliage_chance = disp_bm_chance * selection_chance(x - disp_x, y - disp_y)
    return foliage_chance, bm_for_prod

def get_totals(des_fungi_grid, foliage_grid, bm_for_prod):
    total_fungi = np.sum(des_fungi_grid)
    total_plants = np.sum(foliage_grid)
    bm_for_grow = const.AVG_BM_TO_GROW_FUNG * total_fungi
    bm_total = bm_for_prod + bm_for_grow

    return total_fungi, total_plants, bm_for_grow, bm_total

def calculate_fungus_distribution(length, width, dispensers, disp_coords, fungi_type):
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    fungi_weight = const.WARP_FUNG_CHANCE if fungi_type == WARPED else const.CRMS_FUNG_CHANCE

    foliage_grid, des_fungi_grid, bm_for_prod, disp_foliage_grids, disp_des_fungi_grids = \
        calculate_distribution(length, width, dispensers, disp_coords, fungi_weight, fungi_type)

    total_fungi, total_plants, bm_for_grow, bm_total = \
        get_totals(des_fungi_grid, foliage_grid, bm_for_prod)

    return total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, \
        disp_foliage_grids, disp_des_fungi_grids
