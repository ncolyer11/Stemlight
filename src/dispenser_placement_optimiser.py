import math
import numpy as np
import itertools as iter
import time
from src.Fungus_Distribution_Backend import calculate_fungus_distribution

WARPED = 0
CRIMSON = 1

def generate_permutations(length, width, n):
    # Generate all possible coordinates in the grid
    coordinates = np.mgrid[0:width, 0:length].reshape(2,-1).T.tolist()
    # Generate all permutations of n distinct coordinates
    for c in iter.combinations(coordinates, n):
        for p in iter.permutations(c):
            yield list(p)

def calculate_max_fungi(length, width, num_dispensers, disp_perms, fungus_type):
    max_fungi = 0
    optimal_rates_coords = []
    all_optimal_coords = [optimal_rates_coords]

    for disp_perm in disp_perms:
        _, total_fungi, *_ = \
            calculate_fungus_distribution(length, width, num_dispensers, disp_perm, fungus_type)
        # Update optimal perm for rates if a better combination is found
        if math.isclose(total_fungi, max_fungi, abs_tol=0.000001):
            # Add to collection of optimal coordinates if the same max is found
            all_optimal_coords.append(disp_perm)
        elif total_fungi > max_fungi:
            max_fungi = total_fungi
            optimal_rates_coords = disp_perm
            # Reset collection of optimal coordinates if a new max is found
            all_optimal_coords = [disp_perm]

    return max_fungi, optimal_rates_coords, all_optimal_coords

length = 5
width = 5
num_dispensers = 6
f_type = WARPED
f_type = CRIMSON

permutations = np.math.perm(length * width, num_dispensers)
est_time_to_run = permutations * (1 / 3752.85 if f_type == WARPED else 1 / 3866.68)
    
print(f"Est. runtime: {est_time_to_run:.4f}s ({permutations} permutations) ")
start_time = time.time()
disp_perms = generate_permutations(length, width, num_dispensers)
max_rates, max_rates_coords, all_max_coords = \
    calculate_max_fungi(length, width, num_dispensers, disp_perms, f_type)

print(f'Calculated max fungi in {time.time() - start_time:.3f} seconds')
print(f'Maximum {"crimson" if f_type == CRIMSON else "warped"} fungi: {max_rates:.3f}')
print(f'Optimal coords: {max_rates_coords}')
# Print the location of max_rates_coords in a grid on terminal
for row in range(width):
    for col in range(length):
        if [row, col] in max_rates_coords:
            print(f'[{max_rates_coords.index([row, col])}]', end='')
        else:
            print('[ ]', end='')
    print()
print()

print(f"{len(all_max_coords)} optimal positions found:" )
for i, coords in enumerate(all_max_coords):
    print(f'{i + 1:3}: {coords}')
    for row in range(width):
        if row != 0:
            print()
        print("    ", end='')
        for col in range(length):
            if [row, col] in coords:
                print(f'[{coords.index([row, col])}]', end='')
            else:
                print('[ ]', end='')
    print('\n')
    
# after calculating the most optimal positions to put the dispensers
# it should compare the difference between the worst possible ordering of those dispensers and the
# best to see if it's worth worrying about activation order

# need to conventionally define max bm efficiency first get a useful output
# def calculate_max_fungi():
    # max_bm_effic = 0
    # optimal_effic_coords = []
        # bm_effic = bm_for_prod / total_fungi
        # # Update optimal perm for bm efficiency if a better combination is found
        # if bm_effic > max_bm_effic:
        #     max_bm_effic = bm_effic
        #     optimal_effic_coords = disp_perm

        # return max_bm_effic, optimal_effic_coords

# max_effic, max_effic_coords
# print(f'\nMaximum bm efficiency: {max_effic:.3f}')
# print(f'Optimal coords: {max_effic_coords}')
# # Print the location of max_effic_coords in a grid on terminal
# for i in range(length):
#     for j in range(width):
#         if [i, j] in max_effic_coords:
#             print(f'[{max_effic_coords.index([i, j])}]', end='')
#         else:
#             print('[ ]', end='')
#     print()