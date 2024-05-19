"""A program that helps calculate the optimal position to place n dispensers on a custom size grid of nylium"""

import itertools
import time
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

def calculate_distribution(length, width, dispensers, disp_coords, fungi_weight,
                           fungi, sprouts_total=0, cycles=1, blocked_blocks=[]):
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    # 4D array for storing distribution of foliage for all dispensers and cycles
    disp_foliage_grids = np.zeros((dispensers, cycles, width, length))
    # 2D array for storing distribution of all the foliage
    total_foliage_grid = np.zeros((width, length))

    # 4D array for storing distribution of desired fungus for all dispensers and cycles
    disp_des_fungi_grids = np.zeros((dispensers, cycles, width, length))
    # 2D array for storing distribution of desired fungus
    total_des_fungi_grid = np.zeros((width, length))
    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0

    x, y = np.ogrid[:width, :length]
    for i in range(cycles):
        for j in range(dispensers):
            foliage_chance, bm_for_prod = generate_foliage(disp_coords, total_foliage_grid,
                                                           bm_for_prod, j, x, y)
            for x1, y1 in blocked_blocks:
                foliage_chance[x1][y1] = 0

            des_fungi_chance = foliage_chance * fungi_weight
            disp_des_fungi_grids[j][i] = (1 - total_foliage_grid) * des_fungi_chance
            total_des_fungi_grid += disp_des_fungi_grids[j][i]
            
            disp_foliage_grids[j][i] = (1 - total_foliage_grid) * foliage_chance
            total_foliage_grid += disp_foliage_grids[j][i]
            
            # If warped nylium, generate sprouts
            if fungi == WARPED:
                sprouts_chance = (1 - total_foliage_grid) * foliage_chance
                disp_foliage_grids[j][i] += sprouts_chance
                total_foliage_grid += sprouts_chance
                sprouts_total += sprouts_chance
        
        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for k in range(dispensers):
            # Clear foliage only on top of cleared dispensers except for on the last cycle
            if disp_coords[k][2] == 0 or i == cycles - 1:
                continue
            disp_x, disp_y, _ = disp_coords[k]
            total_foliage_grid[disp_x, disp_y] = 0
            total_des_fungi_grid[disp_x, disp_y] = 0
            disp_foliage_grids[:, :, disp_x, disp_y] = 0
            disp_des_fungi_grids[:, :, disp_x, disp_y] = 0

    return total_foliage_grid, total_des_fungi_grid, bm_for_prod, \
        disp_foliage_grids, disp_des_fungi_grids, sprouts_total

def generate_foliage(disp_coords, foliage_grid, bm_for_prod, i, x, y):
    """Generates the distribution of foliage around a dispenser at a given position"""
    disp_x, disp_y, _ = disp_coords[i]
    disp_bm_chance = 1 - foliage_grid[disp_x, disp_y]
    bm_for_prod += disp_bm_chance

    # P(foliage at x,y) = P(Air above dispensers) * P(x,y being selected)
    foliage_chance = disp_bm_chance * selection_chance(x - disp_x, y - disp_y)
    return foliage_chance, bm_for_prod

def get_totals(des_fungi_grid, foliage_grid, bm_for_prod):
    """Calculates the total amount of foliage, fungi and bone meal required to grow the fungi"""
    total_fungi = np.sum(des_fungi_grid)
    total_foliage = np.sum(foliage_grid)
    bm_for_grow = const.AVG_BM_TO_GROW_FUNG * total_fungi
    bm_total = bm_for_prod + bm_for_grow

    return total_fungi, total_foliage, bm_for_grow, bm_total

def calculate_fungus_distribution(length, width, dispensers, disp_coords, fungi_type,
                                  cycles=1, blocked_blocks=[]):
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    fungi_weight = const.WARP_FUNG_CHANCE if fungi_type == WARPED else const.CRMS_FUNG_CHANCE
    # Keep track of total sprouts to subtract from compost bm as they aren't collected
    sprouts_total = 0
    foliage_grid, des_fungi_grid, bm_for_prod, disp_foliage_grids, \
    disp_des_fungi_grids, sprouts_total = \
        calculate_distribution(length, width, dispensers, disp_coords, fungi_weight,
                               fungi_type, sprouts_total, cycles, blocked_blocks)

    total_des_fungi, total_foliage, bm_for_grow, bm_total = \
        get_totals(des_fungi_grid, foliage_grid, bm_for_prod)

    # Subtract the amount of bone meal retrieved from composting the excess foliage losslessly
    bm_from_compost = (total_foliage - np.sum(sprouts_total) - total_des_fungi ) / const.FOLIAGE_PER_BM
    return {
        "total_foliage": total_foliage,
        "total_des_fungi": total_des_fungi,
        "bm_for_prod": bm_for_prod - bm_from_compost,
        "bm_for_grow": bm_for_grow,
        "bm_total": bm_total,
        "disp_foliage_grids": disp_foliage_grids,
        "disp_des_fungi_grids": disp_des_fungi_grids
    }

def remove_duplicates(nested_list):
    """Remove duplicate sublists from a list of sublists of coordinates"""
    # Convert each sublist of coordinates to a tuple of tuples
    unique_set = {tuple(map(tuple, sublist)) for sublist in nested_list}
    # Convert back to a list of lists
    unique_list = [list(map(list, sublist)) for sublist in unique_set]
    return unique_list

def generate_transformations(coords, l, w):
    """Generate all reflections, rotations, and permutations of the optimal coordinates"""
    alt_coords = []
    for coord in coords:
        transformed_coords = [coord]
        x, y = coord[0:2]
        # 180deg rotation
        transformed_coords.append([w-1-x,l-1-y])
        # 90deg ccw and cw rotations are only equivalent for square grids
        if l == w:
            transformed_coords.append([y,w-1-x])
            transformed_coords.append([l-1-y, x])
        for i, sub_coord in enumerate(transformed_coords):
            if i > 3:
                break
            x1 = sub_coord[0]
            y1 = sub_coord[1]
            # Up/down reflection
            transformed_coords.append([x1, l - 1 - y1])
            # Right/left reflection
            transformed_coords.append([w - 1 - x1, y1])
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

def output_viable_coords(optimal_coords, optimal_value, length, width, wb_per_fungi, fungi_type):
    """Run through all reflections, rotations, and permutations of the optimal coordinates
    and record all solution within 0.1% of the best solution to a file."""
    try:
        start_time = time.time()
        f = open("viable_coords.txt", "w")
        worst_value = optimal_value
        coords_list_metrics = []
        for coords in generate_transformations(optimal_coords, length, width):
            dist_data = calculate_fungus_distribution(
                length,
                width,
                len(coords),
                [[coord[0], coord[1], 0] for coord in coords],
                fungi_type
            )
            total_des_fungi = dist_data["total_des_fungi"]
            bm_for_prod = dist_data["bm_for_prod"]

            bm_req = bm_for_prod < wb_per_fungi / const.WARTS_PER_BM - const.AVG_BM_TO_GROW_FUNG
            if total_des_fungi < optimal_value:
                worst_value = total_des_fungi
            if abs(total_des_fungi - optimal_value) / optimal_value <= 0.0005 and bm_req:
                coords_list_metrics.append((total_des_fungi, bm_for_prod, coords))

        # Sort the list by the desired fungi value
        coords_list_metrics.sort(key=lambda x: x[0], reverse=True)

        # Write the sorted list to the file
        alt_placements = len(coords_list_metrics)
        f.write(f"Number of alternate placements: {alt_placements}\n")
        worst_loss = round((optimal_value - worst_value) / optimal_value * 100, 5)
        lost_f = round(optimal_value - worst_value, 5)
        f.write(f"Max efficiency loss without caring about order: {worst_loss}% ({lost_f} fungi)\n\n")
        for i, (total_des_fungi, bm_for_prod, coords) in enumerate(coords_list_metrics, start=1):
            # Bandaid fix for current out of memory error
            f.write(f"Desired Fungi: {round(total_des_fungi, 5)}\n"
                    f"Bone Meal Used: {round(bm_for_prod, 5)}\n")
            f.write(f"Coords: {coords}\n")
            for y in range(width):
                for x in range(length):
                    if [x, y] in coords:
                        f.write(f"[{coords.index([x, y])}]")
                    else:
                        f.write("[ ]")
                f.write("\n")
            f.write("\n")
        f.close()
        print("Alternate placements calculated in:", round(time.time() - start_time, 3), "seconds")
        return alt_placements
    except Exception as e:
        print("An error has occured whilst finding viable coordinates:", e)
        return e
