"""A program that helps calculate the optimal position to place n dispensers on a custom size grid of nylium"""

import time
import itertools

import numpy as np

from src.Assets.constants import *
from src.Assets.heatmap_data import heatmap_array_xyz
from src.Assets.data_classes import *

DP_VAL = 5
NULL_TIME = 0
MAX_ALL_WIDTH = 10
MAX_ALL_LENGTH = 10
MAX_ALL_CYCLES = 5
ALL_RUN_TIME = 10
MAX_ALL_AVG_NUM_DISPS = 15

def selection_chance(x1, y1):
    """Calculates the probability of a block being selected for 
    foliage generation given its offset from a dispenser"""
    x1 = np.abs(x1).astype(int)
    y1 = np.abs(y1).astype(int)
    # Need to take min of x1 and y1 to avoid index out of bounds as numpy evaluates both branches
    return np.where((x1 > 2) | (y1 > 2), 0, NETHER_FOLIAGE_SEL_CACHE[np.minimum(x1, 2),
                                                                     np.minimum(y1, 2)])

def calculate_distribution(L: PlayerlessCore) -> PlayerlessCoreDistOutput:
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    fungi_weight = WARP_FUNG_CHANCE if L.nylium_type == WARPED else CRMS_FUNG_CHANCE
    sprouts_grid = np.zeros((L.size.length, L.size.width))
    twisting_grid = np.zeros((L.size.length, L.size.width))
    # 4D array for storing distribution of foliage for all dispensers and cycles
    disp_foliage_grids = np.zeros((L.num_disps, L.cycles, L.size.length, L.size.width))
    # 2D array for storing distribution of all the foliage
    total_foliage_grid = np.zeros((L.size.length, L.size.width))

    # 4D array for storing distribution of desired fungus for all dispensers and cycles
    disp_des_fungi_grids = np.zeros((L.num_disps, L.cycles, L.size.length, L.size.width))
    # 2D array for storing distribution of desired fungus
    total_des_fungi_grid = np.zeros((L.size.length, L.size.width))
    row, col = np.ogrid[:L.size.length, :L.size.width]

    # 'bm_for_prod': bone meal used during 1 cycle of firing all the given dispensers
    bm_for_prod = 0.0
    for cycle in range(L.cycles):
        for disp_n in range(L.num_disps):
            foliage_chance, bm_for_prod = generate_foliage(L.disp_coords, total_foliage_grid,
                                                           bm_for_prod, disp_n, row, col)
            for row_b, col_b in L.blocked_blocks:
                foliage_chance[row_b][col_b] = 0

            des_fungi_chance = foliage_chance * fungi_weight
            disp_des_fungi_grids[disp_n][cycle] = (1 - total_foliage_grid) * des_fungi_chance
            total_des_fungi_grid += disp_des_fungi_grids[disp_n][cycle]
            
            disp_foliage_grids[disp_n][cycle] = (1 - total_foliage_grid) * foliage_chance
            total_foliage_grid += disp_foliage_grids[disp_n][cycle]
            
            # If warped nylium, generate sprouts and twisting vines
            if L.nylium_type == WARPED:
                sprouts_chance = (1 - total_foliage_grid) * foliage_chance
                disp_foliage_grids[disp_n][cycle] += sprouts_chance
                total_foliage_grid += sprouts_chance
                sprouts_grid += sprouts_chance
                
                # Math for this was kinda fun actually
                disp_row, disp_col = L.disp_coords[disp_n].row, L.disp_coords[disp_n].col
                new_disp_chance = 1 - total_foliage_grid[disp_row, disp_col]
                twisting_chance = (1 - total_foliage_grid) * TWISTING_SEL_CHANCE \
                                  * np.where((row == disp_row) & (col == disp_col),
                                             1, new_disp_chance)
                disp_foliage_grids[disp_n][cycle] += twisting_chance
                total_foliage_grid += twisting_chance
                twisting_grid += twisting_chance
        
        # Replicate triggering pistons to clear foliage on top of selected dispensers
        for disp in L.disp_coords:
            # Clear foliage only on top of cleared dispensers
            if disp.cleared == CLEARED:
                disp_row, disp_col = disp.row, disp.col
                total_foliage_grid[disp_row, disp_col] = 0
                total_des_fungi_grid[disp_row, disp_col] = 0
                disp_foliage_grids[:, :, disp_row, disp_col] = 0
                disp_des_fungi_grids[:, :, disp_row, disp_col] = 0
                if L.nylium_type == WARPED:
                    sprouts_grid[disp_row, disp_col] = 0
                    twisting_grid[disp_row, disp_col] = 0
    
    return PlayerlessCoreDistOutput(
        total_foliage_grid=total_foliage_grid,
        total_des_fungi_grid=total_des_fungi_grid,
        disp_foliage_grids=disp_foliage_grids,
        disp_des_fungi_grids=disp_des_fungi_grids,
        sprouts_grid=sprouts_grid,
        twisting_grid=twisting_grid,
        bm_for_prod=bm_for_prod
    )

def generate_foliage(disp_coords, foliage_grid, bm_for_prod, disp_n, row,
                     col) -> Tuple[np.ndarray, float]:
    """Generates the distribution of foliage around a dispenser at a given position"""
    disp_row, disp_col = disp_coords[disp_n].row, disp_coords[disp_n].col
    disp_bm_chance = 1 - foliage_grid[disp_row, disp_col]
    bm_for_prod += disp_bm_chance

    # P(foliage at row, col) = P(Air above dispensers) * P(row, col being selected)
    # Note, don't double multiply the chance of air above the position if it's at the dispenser
    foliage_chance = np.where((row == disp_row) & (col == disp_col), 1, disp_bm_chance) \
                     * selection_chance(row - disp_row, col - disp_col)
    return foliage_chance, bm_for_prod

def get_totals(D: PlayerlessCoreDistOutput) -> Tuple[float, float, float]:
    """Calculates the total amount of foliage, fungi and bone meal required to grow the fungi"""
    total_fungi = np.sum(D.total_des_fungi_grid)
    # Total foliage EXCLUDES desired fungi and sprouts, and 2 / 3 of twisting vines don't drop
    print(f"total_foliage: {np.sum(D.total_foliage_grid)}")
    print(f"twisting: {np.sum(D.twisting_grid)}")
    total_foliage = np.sum(D.total_foliage_grid - D.sprouts_grid
                           - 2 * D.twisting_grid / 3) - total_fungi
    print(f"new total_foliage: {total_foliage}")
    bm_for_grow = AVG_BM_TO_GROW_FUNG * total_fungi

    return total_fungi, total_foliage, bm_for_grow

def calculate_fungus_distribution(L: PlayerlessCore) -> PlayerlessCoreOutput:
    """Calculates the distribution of foliage and fungi on a custom size grid of nylium"""
    L.disp_coords.sort(key=lambda d: d.timestamp)

    out = calculate_distribution(L)
    # Total foliage EXCLUDES desired fungi and sprouts
    total_des_fungi, total_foliage, bm_for_grow = get_totals(out)

    # Subtract the bit of bone meal retrieved from composting the excess foliage at 82.5% efficiency
    bm_from_compost = (FOLIAGE_COLLECTION_EFFIC * total_foliage) / FOLIAGE_PER_BM
    
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
    # Avoid recalculating fungus distribution if it's already been calculated
    if dist_data is None:
        dist_data = calculate_fungus_distribution(L)
    
    des_fungi_grid = np.sum(dist_data.disp_des_fungi_grids, axis=(0, 1))
    bm_for_prod = dist_data.bm_for_prod
    p_width = L.size.width
    p_length = L.size.length

    hf_width = NT_MAX_RAD + p_width + NT_MAX_RAD
    hf_length = NT_MAX_RAD + p_length + NT_MAX_RAD
    hf_grids = np.zeros((
        len(BLOCK_TYPES) + 1,
        hf_width,
        hf_length,
        NT_MAX_HT
    ))

    # Iterate through each x,z coord in the nylium grid/platform
    for nylium_x, nylium_z in itertools.product(range(p_length), range(p_width)):
        # Generation order is Stems -> Shrooms -> Warts
        for b in range(len(BLOCK_TYPES)):
            # Calculate weighted chance for all y,z,x coordinates
            fungus_chance = des_fungi_grid[nylium_x, nylium_z]
            y_range, z_range, x_range = range(NT_MAX_HT), range(NT_MAX_WD), range(NT_MAX_WD)
            for y, z, x in itertools.product(y_range, z_range, x_range):
                weighted_chance = fungus_chance * heatmap_array_xyz[b, NT_MAX_HT - y - 1, z, x]
                curr = hf_grids[3, nylium_z + z, nylium_x + x, y]

                gen_chance = (1 - curr) * weighted_chance
                hf_grids[b, nylium_z + z, nylium_x + x, y] += gen_chance
                hf_grids[3, nylium_z + z, nylium_x + x, y] += gen_chance

    total_wb = np.sum(hf_grids[2]) * L.blast_chamber_effic
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
    l = s.length
    w = s.width
    coords = [[coord.row, coord.col, coord.cleared] for coord in coords]
    for coord in coords:
        transformed_coords = [coord]
        # cs: cleared status
        row, col, cs = coord
        # 180deg rotation
        transformed_coords.append([l-1-row, w-1-col, cs])
        # 90deg ccw and cw rotations are only equivalent for square grids
        if l == w:
            transformed_coords.append([col, l-1-row, cs])
            transformed_coords.append([w-1-col, row, cs])
        for i, sub_coord in enumerate(transformed_coords):
            if i > 3:
                break
            row1 = sub_coord[0]
            col1 = sub_coord[1]
            # Up/down reflection
            transformed_coords.append([row1, w-1-col1, cs])
            # Right/left reflection
            transformed_coords.append([l-1-row1, col1, cs])
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

def output_viable_coords(L: PlayerlessCore, optimal_coords, optimal_value):
    """Run through all reflections, rotations, and permutations of the optimal coordinates
    and record all solution within 0.1% of the best solution to a file."""
    # try:
    start_time = time.time()
    org_disp_coords = L.disp_coords
    worst_value = optimal_value
    coords_list_metrics = []
    for coords in generate_transformations(optimal_coords, L.size):
        L.disp_coords = [
            Dispenser(coords[0], coords[1], NULL_TIME, coords[2]) for coords in coords
        ]
        dist_data = calculate_fungus_distribution(L)
        total_des_fungi = dist_data.total_des_fungi
        bm_for_prod = dist_data.bm_for_prod

        bm_req = bm_for_prod < L.wb_per_fungus / WARTS_PER_BM - AVG_BM_TO_GROW_FUNG
        if total_des_fungi < worst_value and bm_req:
            worst_value = total_des_fungi
        if abs(total_des_fungi - optimal_value) / optimal_value <= 0.001 and bm_req:
            coords_list_metrics.append((total_des_fungi, bm_for_prod, coords))

    # Sort the list by the desired fungi value
    coords_list_metrics.sort(key=lambda row: row[0], reverse=True)
    L.disp_coords = org_disp_coords
    return export_alt_placements(L.size, coords_list_metrics, optimal_value,
                                    worst_value, start_time, L.blocked_blocks)
    # except Exception as e:
    #     print("An error has occured whilst finding viable coordinates:", e)
    #     return e

def export_alt_placements(size: Dimensions, metrics, optimal_value, worst_value, start_time,
                          blocked_blocks) -> int:
    """Write the sorted list to a file"""
    num_alt_placements = len(metrics)
    f = open("Alternate Dispenser Placements.txt", "w")
    f.write(f"Number of alternate placements: {num_alt_placements}\n")
    lost_f = optimal_value - worst_value
    worst_loss = round(lost_f / optimal_value * 100, 5)
    lost_f = round(lost_f, 5)
    f.write(f"Max efficiency loss without caring about order: {worst_loss}% ({lost_f} fungi/cycle)\n\n")
    for i, (total_des_fungi, bm_for_prod, placements) in enumerate(metrics, start=1):
        coords = [[pos[0], pos[1]] for pos in placements]
        coords_str = '['
        for j, (row, col) in enumerate(coords):
            if [row, col, CLEARED] in placements:
                coords_str += '{' + str(row) + ', ' + str(col) + '}'
            else:
                coords_str += '[' + str(row) + ', ' + str(col) + ']'
            
            if j != len(coords) - 1:
                coords_str += ', '
            else:
                coords_str += ']'
            
        f.write(f"#{i}:\n")
        f.write(f"Desired Fungi: {round(total_des_fungi, 5)}\n"
                f"Bone Meal Used: {round(bm_for_prod, 5)}\n")
        f.write(f"Coords: {coords_str}\n")
        for row in range(size.length):
            for col in range(size.width):
                if [row, col, UNCLEARED] in placements:
                    f.write(f"[{coords.index([row, col]) + 1}]")
                elif [row, col, CLEARED] in placements:
                    f.write("{" + str(coords.index([row, col]) + 1) + "}")
                elif (row, col) in blocked_blocks:
                    f.write("[/]")
                else:
                    f.write("[ ]")
            f.write("\n")
        f.write("\n")
    f.close()
    print("Alternate placements calculated in:", round(time.time() - start_time, 3), "seconds")
    return num_alt_placements