import numpy as np
import itertools
import time
from src.Fungus_Distribution_Backend import calculate_fungus_distribution

WARPED = 0
CRIMSON = 1

def generate_permutations(length, width, n):
    # Generate all possible coordinates in the grid
    coordinates = np.mgrid[0:width, 0:length].reshape(2,-1).T.tolist()

    # Generate all permutations of n distinct coordinates
    for c in itertools.combinations(coordinates, n):
        for p in itertools.permutations(c):
            yield list(p)

def calculate_max_fungi(length, width, num_dispensers, disp_perms, fungus_type):
    max_fungi = 0
    optimal_rates_coords = []

    for disp_perm in disp_perms:
        _, total_fungi, bm_for_prod, *_ = \
            calculate_fungus_distribution(length, width, num_dispensers, disp_perm, fungus_type)
        # Update optimal perm for rates if a better combination is found
        if total_fungi > max_fungi:
            max_fungi = total_fungi
            optimal_rates_coords = disp_perm

    # for i in range(length):
    #     for j in range(width):
    #         if [i, j] in optimal_rates_coords:
    #             print(f'[{optimal_rates_coords.index([i, j])}]', end='')
    #         else:
    #             print('[ ]', end='')
    #     print()
    # print()
    return max_fungi, optimal_rates_coords

length = 5
width = 5
num_dispensers = 4
f_type = CRIMSON
f_type = WARPED

start_time = time.time()
disp_perms = generate_permutations(length, width, num_dispensers)
max_rates, max__rates_coords = calculate_max_fungi(length, width, num_dispensers, disp_perms, f_type)

print(f'Calculated max fungi in {time.time() - start_time:.3f} seconds')
print(f'Maximum {"crimson" if f_type == CRIMSON else "warped"} fungi: {max_rates:.3f}')
print(f'Optimal coords: {max__rates_coords}')
# Print the location of max__rates_coords in a grid on terminal
for i in range(length):
    for j in range(width):
        if [i, j] in max__rates_coords:
            print(f'[{max__rates_coords.index([i, j])}]', end='')
        else:
            print('[ ]', end='')
    print()


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