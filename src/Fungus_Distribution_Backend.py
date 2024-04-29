"""A program that helps calculate the optimal position to place n dispensers on a custom size grid of nylium"""

import random
import numpy as np
import itertools as iter
import time

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
    # 2D Array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))
    # 2D Array for storing distribution of desired fungus
    des_fungi_grid = np.zeros((width, length))
    # Bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0

    x, y = np.ogrid[:width, :length]
    # Moving if statement outside the loop so it's only checked once
    if fungi == 1:
        for i in range(dispensers):
            foliage_chance, bm_for_prod = generate_foliage(disp_coords, foliage_grid, bm_for_prod, i, x, y)
            # (1 - foliage_grid): P(Air at x,y)
            np.add(foliage_grid, (1 - foliage_grid) * foliage_chance, out=foliage_grid)

        # If crimson, can factor out the crimson fungi weight and multiply it at the very end
        des_fungi_grid = fungi_weight * foliage_grid
    else:
        for i in range(dispensers):
            foliage_chance, bm_for_prod = \
                generate_foliage(disp_coords, foliage_grid, bm_for_prod, i, x, y)
            des_fungi_chance = foliage_chance * fungi_weight
            
            np.add(des_fungi_grid, (1 - foliage_grid) * des_fungi_chance, out=des_fungi_grid)
            np.add(foliage_grid, (1 - foliage_grid) * foliage_chance, out=foliage_grid)
            # If warped nylium, generate sprouts
            np.add(foliage_grid, (1 - foliage_grid) * foliage_chance, out=foliage_grid)

    return foliage_grid, des_fungi_grid, bm_for_prod

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

def print_results(total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, fungi_type):
    print(f'Total plants: {round(total_plants, DP_VAL)}')
    if fungi_type == WARPED:
        print(f'Warped fungi: {round(total_fungi, DP_VAL)}')
    else:
        print(f'Crimson fungi: {round(total_fungi, DP_VAL)}')
    print(f'Bone meal used per cycle (to produce + to grow):\n'
            f'{round(bm_for_prod, DP_VAL)} + {round(bm_for_grow, DP_VAL)} = '
            f'{round(bm_total, DP_VAL)}')

def calculate_fungus_distribution(length, width, dispensers, disp_coords, fungi_type):
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    fungi_weight = const.WARP_FUNG_CHANCE if fungi_type == WARPED else const.CRMS_FUNG_CHANCE

    foliage_grid, des_fungi_grid, bm_for_prod = \
        calculate_distribution(length, width, dispensers, disp_coords, fungi_weight, fungi_type)

    total_fungi, total_plants, bm_for_grow, bm_total = \
        get_totals(des_fungi_grid, foliage_grid, bm_for_prod)

    # print_results(total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, fungi_type)
    return total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, fungi_type
