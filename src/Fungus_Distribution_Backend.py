"""A program that helps calculate the optimal position to place n dispensers on a custom size grid of nylium"""

import random
import numpy as np
import itertools as iter
import time

from src.Assets import constants as const

DP_VAL = 5
WARPED = 0
CRIMSON = 1
SPREAD_AMOUNT = const.FUNG_SPREAD_RAD ** 4
SPREAD_AREA = const.FUNG_SPREAD_RAD ** 2

def selection_chance(x1, y1):
    # Neat little formula cooked up on Desmos
    x2 = const.FUNG_SPREAD_RAD - np.abs(x1)
    y2 = const.FUNG_SPREAD_RAD - np.abs(y1)
    P_block = np.where((x2 < 0) | (y2 < 0), 0, x2 * y2 / SPREAD_AMOUNT)

    # Calculate binomial distribution using numpy's vectorized operations
    k = np.arange(1, SPREAD_AREA + 1)
    P = np.sum((1 - P_block[..., None]) ** (SPREAD_AREA - k), axis=-1)

    return P * P_block

def calculate_distribution(length, width, dispensers, disp_coords, fungi_weight, fungi):
    # 2D Array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))
    # 2D Array for storing distribution of desired fungus
    des_fungi_grid = np.zeros((width, length))
    # Bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0

    x, y = np.ogrid[:width, :length]
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

    # P(foliage at x,y) = P(Air above dispensers) * P(x,y being selected) * 
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
    fungi_weight = 0
    if fungi_type == WARPED:
        fungi_weight = const.WARP_FUNG_CHANCE
    else:
        fungi_weight = const.CRMS_FUNG_CHANCE
    foliage_grid, des_fungi_grid, bm_for_prod = \
        calculate_distribution(length, width, dispensers, disp_coords, fungi_weight, fungi_type)

    total_fungi, total_plants, bm_for_grow, bm_total = \
        get_totals(des_fungi_grid, foliage_grid, bm_for_prod)

    # print_results(total_plants, total_fungi, bm_for_prod, 
                #   bm_for_grow, bm_total, fungi_type)
    return total_plants, total_fungi, bm_for_prod, bm_for_grow, bm_total, fungi_type
