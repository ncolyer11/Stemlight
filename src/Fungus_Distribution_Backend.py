"""A program that helps calculate the optimal position to place n dispensers on a custom size grid of nylium"""

import time
import copy
import itertools
import numpy as np

from src.Assets import constants as const
from src.Fast_Dispenser_Distribution import fast_calc_fung_dist, fast_calc_hf_dist
from src.Assets.heatmap_data import heatmap_array_xyz
from src.Assets.data_classes import *

DP_VAL = 5
WARPED = 0
CRIMSON = 1
UNCLEARED = 0
CLEARED = 1

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

def calculate_distribution(L: PlayerlessCore) -> PlayerlessCoreDistOutput:
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    fungi_weight = const.WARP_FUNG_CHANCE if L.nylium_type == WARPED else const.CRMS_FUNG_CHANCE
    sprouts_total = np.zeros((L.size.length, L.size.width))
    # 4D array for storing distribution of foliage for all dispensers and cycles
    disp_foliage_grids = np.zeros((L.num_disps, L.cycles, L.size.length, L.size.width))
    # 2D array for storing distribution of all the foliage
    total_foliage_grid = np.zeros((L.size.length, L.size.width))

    # 4D array for storing distribution of desired fungus for all dispensers and cycles
    disp_des_fungi_grids = np.zeros((L.num_disps, L.cycles, L.size.length, L.size.width))
    # 2D array for storing distribution of desired fungus
    total_des_fungi_grid = np.zeros((L.size.length, L.size.width))
    x, y = np.ogrid[:L.size.length, :L.size.width]

    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0
    for i in range(L.cycles):
        for j in range(L.num_disps):
            foliage_chance, bm_for_prod = generate_foliage(L.disp_coords, total_foliage_grid,
                                                           bm_for_prod, j, x, y)
            for x1, y1 in L.blocked_blocks:
                foliage_chance[x1][y1] = 0

            des_fungi_chance = foliage_chance * fungi_weight
            disp_des_fungi_grids[j][i] = (1 - total_foliage_grid) * des_fungi_chance
            total_des_fungi_grid += disp_des_fungi_grids[j][i]
            
            disp_foliage_grids[j][i] = (1 - total_foliage_grid) * foliage_chance
            total_foliage_grid += disp_foliage_grids[j][i]
            
            # If warped nylium, generate sprouts
            if L.nylium_type == WARPED:
                sprouts_chance = (1 - total_foliage_grid) * foliage_chance
                disp_foliage_grids[j][i] += sprouts_chance
                total_foliage_grid += sprouts_chance
                sprouts_total += sprouts_chance
        
        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for k in range(L.num_disps):
            # Clear foliage only on top of cleared dispensers
            if L.disp_coords[k][2] == 0:
                continue
            disp_x, disp_y, _ = L.disp_coords[k]
            total_foliage_grid[disp_x, disp_y] = 0
            total_des_fungi_grid[disp_x, disp_y] = 0
            disp_foliage_grids[:, :, disp_x, disp_y] = 0
            disp_des_fungi_grids[:, :, disp_x, disp_y] = 0
            if L.fungi == WARPED:
                sprouts_total[disp_x, disp_y] = 0
    
    return PlayerlessCoreDistOutput(
        total_foliage_grid=total_foliage_grid,
        total_des_fungi_grid=total_des_fungi_grid,
        disp_foliage_grids=disp_foliage_grids,
        disp_des_fungi_grids=disp_des_fungi_grids,
        sprouts_total=sprouts_total,
        bm_for_prod=bm_for_prod
    )

def generate_foliage(disp_coords, foliage_grid, bm_for_prod, i, x, y):
    """Generates the distribution of foliage around a dispenser at a given position"""
    disp_x, disp_y, _ = disp_coords[i]
    disp_bm_chance = 1 - foliage_grid[disp_x, disp_y]
    bm_for_prod += disp_bm_chance

    # P(foliage at x,y) = P(Air above dispensers) * P(x,y being selected)
    # Note, don't double multiply the chance of air above the position if it's at the dispenser
    foliage_chance = np.where((x == disp_x) & (y == disp_y), 1, disp_bm_chance) \
                     * selection_chance(x - disp_x, y - disp_y)
    return foliage_chance, bm_for_prod

def get_totals(des_fungi_grid, foliage_grid):
    """Calculates the total amount of foliage, fungi and bone meal required to grow the fungi"""
    total_fungi = np.sum(des_fungi_grid)
    total_foliage = np.sum(foliage_grid)
    bm_for_grow = const.AVG_BM_TO_GROW_FUNG * total_fungi

    return total_fungi, total_foliage, bm_for_grow

def calculate_fungus_distribution(L: PlayerlessCore) -> PlayerlessCoreOutput:
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    L.disp_coords.sort(key=lambda d: d[2])
    L_org_disp_coords = L.disp_coords.copy()
    L.disp_coords = [(d[0], d[1], d[3]) for d in L.disp_coords]

    # Keep track of total sprouts to subtract from compost bm as they aren't collected
    out = calculate_distribution(L)

    total_des_fungi, total_foliage, bm_for_grow = get_totals(out.total_des_fungi_grid, out.total_foliage_grid)

    # Subtract the amount of bone meal retrieved from composting the excess foliage losslessly
    composted_foliage = total_foliage - np.sum(out.sprouts_total) - total_des_fungi
    bm_from_compost = (const.FOLIAGE_COLLECTION_EFFIC * composted_foliage) / const.FOLIAGE_PER_BM
    
    # Add back time values
    L.disp_coords = L_org_disp_coords
    return PlayerlessCoreOutput(
        total_foliage=total_foliage,
        total_des_fungi=total_des_fungi,
        bm_for_prod=out.bm_for_prod - bm_from_compost,
        bm_for_grow=bm_for_grow,
        bm_total=out.bm_for_prod + bm_for_grow,
        disp_foliage_grids=out.disp_foliage_grids,
        disp_des_fungi_grids=out.disp_des_fungi_grids
    )

def calc_huge_fungus_distribution(
    L: PlayerlessCore, 
    dist_data: PlayerlessCoreOutput = None
) -> Tuple[float, float]:
    """
    Approximately calculates huge fungi generation based off desired fungus distribution
    """
    # Only approximately as calculating the expected wart block distribution given an expected 
    # warped fungi distribution relies on a heap of interacting variables and also that's not even
    # inclduing the fact wart blocks from some early-grown fungi can act as pre-placed wart blocks
    # and can cause VRM in later grown fungi

    # Return early if grid is empty
    if len(L.disp_coords) == 0:
        return 0.0, 0.0
    # Growing after all produced, makes the same output as growing after each cycle
    if dist_data is None:
        dist_data = calculate_fungus_distribution(L)
    
    des_fungi_grid = np.sum(dist_data.disp_des_fungi_grids, axis=(0, 1))
    bm_for_prod = dist_data.bm_for_prod
    p_width = L.size.width
    p_length = L.size.length

    hf_width = const.NT_MAX_RAD + p_width + const.NT_MAX_RAD
    hf_length = const.NT_MAX_RAD + p_length + const.NT_MAX_RAD
    hf_grids = np.zeros((
        len(const.BLOCK_TYPES) + 1,
        hf_width,
        hf_length,
        const.NT_MAX_HT
    ))

    # Iterate through each x,z coord in the nylium grid/platform
    for nylium_x, nylium_z in itertools.product(range(p_length), range(p_width)):
        # Generation order is Stems -> Shrooms -> Warts
        for b in range(len(const.BLOCK_TYPES)):
            # Calculate weighted chance for all y,z,x coordinates
            fungus_chance = des_fungi_grid[nylium_x, nylium_z]
            y_range, z_range, x_range = range(const.NT_MAX_HT), range(const.NT_MAX_WD), range(const.NT_MAX_WD)
            for y, z, x in itertools.product(y_range, z_range, x_range):
                weighted_chance = fungus_chance * heatmap_array_xyz[b, const.NT_MAX_HT - y - 1, z, x]
                curr = hf_grids[3, nylium_z + z, nylium_x + x, y]

                gen_chance = (1 - curr) * weighted_chance
                hf_grids[b, nylium_z + z, nylium_x + x, y] += gen_chance
                hf_grids[3, nylium_z + z, nylium_x + x, y] += gen_chance

    total_wb = np.sum(hf_grids[2]) * float(L.blast_chamber_effic.get())
    return total_wb, bm_for_prod


def remove_duplicates(nested_list):
    """Remove duplicate sublists from a list of sublists of coordinates"""
    # Convert each sublist of coordinates to a tuple of tuples
    unique_set = {tuple(map(tuple, sublist)) for sublist in nested_list}
    # Convert back to a list of lists
    unique_list = [list(map(list, sublist)) for sublist in unique_set]
    return unique_list

def generate_transformations(coords, s: Dimensions):
    """Generate all reflections, rotations, and permutations of the optimal coordinates"""
    alt_coords = []
    w = s.width
    l = s.length
    for coord in coords:
        transformed_coords = [coord]
        # cs: cleared status
        x, y, cs = coord
        # 180deg rotation
        transformed_coords.append([w-1-x, l-1-y, cs])
        # 90deg ccw and cw rotations are only equivalent for square grids
        if l == w:
            transformed_coords.append([y, w-1-x, cs])
            transformed_coords.append([l-1-y, x, cs])
        for i, sub_coord in enumerate(transformed_coords):
            if i > 3:
                break
            x1 = sub_coord[0]
            y1 = sub_coord[1]
            # Up/down reflection
            transformed_coords.append([x1, l-1-y1, cs])
            # Right/left reflection
            transformed_coords.append([w-1-x1, y1, cs])
        alt_coords.append(transformed_coords)
    alt_placements = []
    # Grab equally transformed sets of coords to group into consecutive sets of alternate optimal coords
    for i in range(len(alt_coords[0])):
        alt_placements.append([coords[i] for coords in alt_coords])

    # Skip if there are more than 8 dispensers as the number of permutations is too high
    if len(coords) > 8:
        return remove_duplicates(alt_placements)
    
    # Generate all permutations of dispenser order including new reflections and rotations
    perms = []
    for placement in alt_placements:
        sub_perms = list(itertools.permutations(placement))
        sub_perms_list = [list(perm) for perm in sub_perms]
        perms.extend(sub_perms_list)
    # Remove duplicate permutations to lower computation time
    return remove_duplicates(perms)

def output_viable_coords(L: PlayerlessCore, optimal_coords, optimal_value, wb_per_fungi):
    """Run through all reflections, rotations, and permutations of the optimal coordinates
    and record all solution within 0.1% of the best solution to a file."""
    optimal_func = fast_calc_fung_dist  # Keeping possible future functionality
                                        # for other functions to optimise
    try:
        start_time = time.time()
        worst_value = optimal_value
        coords_list_metrics = []
        for coords in generate_transformations(optimal_coords, L.size):
            if optimal_func == fast_calc_fung_dist:
                dist_data = calculate_fungus_distribution(L)
                total_des_fungi = dist_data.total_des_fungi
                bm_for_prod = dist_data.bm_for_prod
            else:
                total_wart_blocks, bm_for_prod = \
                fast_calc_hf_dist(
                    L.size.length,
                    L.size.width,
                    L.nylium_type,
                    L.disp_coords,
                    L.cycles,
                    L.blocked_blocks,
                )
                # Got a headache atm
                total_des_fungi = 0

            bm_req = bm_for_prod < wb_per_fungi / const.WARTS_PER_BM - const.AVG_BM_TO_GROW_FUNG
            if total_des_fungi < worst_value and bm_req:
                worst_value = total_des_fungi
            if abs(total_des_fungi - optimal_value) / optimal_value <= 0.001 and bm_req:
                coords_list_metrics.append((total_des_fungi, bm_for_prod, coords))

        # Sort the list by the desired fungi value
        coords_list_metrics.sort(key=lambda x: x[0], reverse=True)
        return export_alt_placements(L.size, coords_list_metrics, optimal_value,
                                     worst_value, start_time, L.blocked_blocks)
    except Exception as e:
        print("An error has occured whilst finding viable coordinates:", e)
        return e

def export_alt_placements(size: Dimensions, metrics, optimal_value, worst_value, start_time,
                          blocked_blocks):
    """Write the sorted list to a file"""
    alt_placements = len(metrics)
    f = open("Alternate Dispenser Placements.txt", "w")
    f.write(f"Number of alternate placements: {alt_placements}\n")
    lost_f = optimal_value - worst_value
    worst_loss = round(lost_f / optimal_value * 100, 5)
    lost_f = round(lost_f, 5)
    f.write(f"Max efficiency loss without caring about order: {worst_loss}% ({lost_f} fungi/cycle)\n\n")
    for i, (total_des_fungi, bm_for_prod, placements) in enumerate(metrics, start=1):
        coords = [[pos[0], pos[1]] for pos in placements]
        f.write(f"#{i}:\n")
        f.write(f"Desired Fungi: {round(total_des_fungi, 5)}\n"
                f"Bone Meal Used: {round(bm_for_prod, 5)}\n")
        f.write(f"Coords: {coords}\n")
        for x in range(size.width):
            for y in range(size.length):
                if [x, y, UNCLEARED] in placements:
                    f.write(f"[{coords.index([x, y]) + 1}]")
                elif [x, y, CLEARED] in placements:
                    f.write("{" + str(coords.index([x, y]) + 1) + "}")
                elif [x, y] in blocked_blocks:
                    f.write("[/]")
                else:
                    f.write("[ ]")
            f.write("\n")
        f.write("\n")
    f.close()
    print("Alternate placements calculated in:", round(time.time() - start_time, 3), "seconds")
    return alt_placements
