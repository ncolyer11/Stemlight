import ast
import math
import numpy as np
import itertools as itertools
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

def brute_force_max_fungi(length, width, num_dispensers, disp_perms, num_perms, fungus_type):
    max_fungi = 0
    optimal_rates_coords = []
    all_optimal_coords = [optimal_rates_coords]

    # For large searches, optimal solution is most likely within the first 1/3 of the perms
    limiter = num_perms if num_perms < 1e4 else num_perms // 3
    # First 10% of perms are clumped perms around the top 2 rows
    for disp_perm in itertools.islice(disp_perms, num_perms // 10, limiter):
    # for disp_perm in disp_perms:
        _, total_fungi, *_ = \
            calculate_fungus_distribution(length, width, num_dispensers, disp_perm, fungus_type)
        # Update optimal perm for rates if a better combination is found
        if math.isclose(total_fungi, max_fungi, abs_tol=1e-7):
            # Add to collection of optimal coordinates if the same max is found
            all_optimal_coords.append(disp_perm)
        elif total_fungi > max_fungi:
            max_fungi = total_fungi
            optimal_rates_coords = disp_perm
            # Reset collection of optimal coordinates if a new max is found
            all_optimal_coords = [disp_perm]


    return max_fungi, optimal_rates_coords, all_optimal_coords

def dracolyer(length, width, num_dispensers, fungi_type):
    """
    ### The Dracolyer algorithm is a greedy algorithm that optimises the placement of dispensers:
    For a 5x5 grid:
    - Start with optimising for 1 dispenser
    - To optimise, the algorithm should go through every block and track the foliage added taking
    into account current foliage on the platform
    - It should also track the decrease in foliage caused by generating foliage on top of other dispensers
    - It should place the dispenser in a position that maximises added_foliage - decreased_foliage
    - After one dispenser is placed, the algorithm should move on to the next dispenser
    - Afte the next dispenser is placed, the algorithm should go back and optimise the previous dispenser again
    - If the algorithm finds a better position for the previous dispenser, it should update the position
    and then optimise the next dispenser again
    - This process continues until the previous and current optimised positions are the same
    - Then the algorithm should move on to the next dispenser and repeat the process 
    """
    # Handle 0 dispensers
    if num_dispensers == 0:
        return 0, []

    disp_positions = []
    # Start optimisation

    # To make the algo less greedy, I think it should try optimising all current dispensers,
    # and only update the one that yielded the highest results for that iteration
    # I worry that the algorithm isn't looking ahead enough so it's getting stuck on local maximums
    start_time = time.time()
    for n in range(num_dispensers):
        disp_positions.append([0,0])
        prev_positions = None
        l = 0
        # print("====================================")
        while disp_positions != prev_positions:
            # To stop users' clients from freezing
            if time.time() - start_time > 20:
                return -1, [], [[]]
            prev_positions = disp_positions.copy()
            for i in range(n, 0, -1):
                disp_positions[i] = optimise_dispenser(i, disp_positions, length, width, fungi_type)
                # print("   back: ", i, disp_positions, "\n")
            for i in range(n + 1):
                disp_positions[i] = optimise_dispenser(i, disp_positions, length, width, fungi_type)
                # print("forward: ", i, disp_positions)
            l += 1
        # print("====================================\n")

    return 1, disp_positions, [disp_positions]

def optimise_dispenser(disp_index, disp_positions, length, width, fungi_type):
    """Find the position that results in the most foliage when a new dispenser is placed there
    given a pre-exisiting nylium grid with other dispensers"""
    max_foliage = -1e3
    max_pos = None
    # Try placing the dispenser at every position in the grid
    for i, j in itertools.product(range(width), range(length)):
        # print(f"Optimising dispenser {disp_index + 1}/{len(disp_positions)} at {i}, {j}")
        # print(f"Foliage: {max_foliage} at {max_pos}")
        if [i, j] in disp_positions:
            # actually ffs you should compare to see if placing the currently selected dispenser
            # at this overlap spot is more optimal than the pre-exisiting one
            continue
        # Place the dispenser
        disp_positions[disp_index] = [i, j]
        # Calculate the total foliage
        total_foliage_added, _, _, _, _, disp_foliage_grids, _ = \
            calculate_fungus_distribution(length, width, len(disp_positions), 
                                          disp_positions, fungi_type)
        total_foliage_blocked = 0
        for k in range(len(disp_positions)):
            if k != disp_index:
                blocked_x = disp_positions[k][0]
                blocked_y = disp_positions[k][1]
                block_chance = disp_foliage_grids[disp_index][blocked_x][blocked_y]
                # print(f"Blocked: {block_chance} at {blocked_x}, {blocked_y}")
                # print(f"Blocked: {np.sum(disp_foliage_grids[k], axis=0)}")
                total_foliage_blocked += block_chance * np.sum(disp_foliage_grids[k])

        # Ok something I think each dispenser optimistation should factor in, is the cost of placing 
        # a dispenser towards the centre/middle as currently the algorithm isn't explicitly taking 
        # into account the effect of greedily placing a dispenser in the current most optimal 
        # position, it should look ahead somehow and take into account the amount of remaining 
        # dispensers left to place down before chosing it's first optimal spot
        
        # If this position results in more foliage, update the max
        total_foliage = total_foliage_added - total_foliage_blocked
        # print(f"Total foliage blocked: {total_foliage_blocked}")
        if total_foliage > max_foliage:
            max_foliage = total_foliage
            max_pos = [i, j]
       
    return max_pos

def find_optimal_indexes(length, width, num_dispensers):
    """Find the indexes of the optimal permutations in the list of all permutations"""
    disp_perms = generate_permutations(length, width, num_dispensers)
    line_list = []
    # Paste in optimal coords into file and set below limiter to the number of optimal coords
    with open('all_6_w_optimal.txt', 'r') as file:
        for line in file:
            line_list.append(ast.literal_eval(line.strip()))

    optimal_perm = 0
    indexes = []
    for i, perm in enumerate(disp_perms):
        if perm == line_list[optimal_perm]:
            optimal_perm += 1
            indexes.append(i)
            if optimal_perm > 383:
                break
    for i in indexes:
        print(i)

def output_data(start_time, f_type, width, length, max_rates, max_rates_coords, all_max_coords):
    """Output the data to the terminal and a file"""
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

    print(f"{len(all_max_coords)} optimal positions found (see file)" )
    with open('optimal_placements.txt', 'w') as file:
        file.write(f'{len(all_max_coords)} optimal positions found:')
        for i, coords in enumerate(all_max_coords):
            file.write(f'{i + 1:3}: {coords}\n')
            for row in range(width):
                if row != 0:
                    file.write('\n')
                file.write("    ")
                for col in range(length):
                    if [row, col] in coords:
                        file.write(f'[{coords.index([row, col])}]')
                    else:
                        file.write('[ ]')
            file.write('\n\n')

def initialise_optimisation(length, width, num_dispensers, f_type):
    """Initialise the optimisation process by taking user input and calculating the runtime"""
    permutations = np.math.perm(length * width, num_dispensers)
    # Time complexity ain't precise coz surprise Python is an interpreted language :p
    # 'k' is now outdated due to storing foliage data across an array of all dispensers
    # k = 1 / 669486 if f_type == WARPED else 1 / 832608
    # est_time_to_run =  k * length * width * num_dispensers * permutations
    # print(f"Est. runtime: {est_time_to_run:.4f}s ({permutations} permutations) ")
    start_time = time.time()

    # find_optimal_indexes(length, width, num_dispensers)
    disp_perms = generate_permutations(length, width, num_dispensers)
    # If the number of permutations is less than 350k, use brute force (TBD, new algo for all rn)
    if permutations < 350e3:
        max_rates, max_rates_coords, all_max_coords = \
            brute_force_max_fungi(length, width, num_dispensers, disp_perms, permutations, f_type)
    # Otherwise, use the more efficient, but still unfinished Dracolyer algorithm
    else:
        max_rates, max_rates_coords, all_max_coords = \
            dracolyer(length, width, num_dispensers, f_type)
    
    # If manually running the optimisation algorithm output data to terminal as well
    if __name__ == "__main__":
        output_data(start_time, f_type, width, length, max_rates, max_rates_coords, all_max_coords)
    # else:
        # print("Dispensers optimised in: ", time.time() - start_time, "seconds")
        # print("Max rates: ", max_rates, "at", max_rates_coords, "wowowo")

    return all_max_coords if max_rates != -1 else -1
    
# For manually running the optimisation algorithm
if __name__ == "__main__":
    length = 1
    width = 5
    num_dispensers = int(input("Enter number of dispensers: "))
    f_type = WARPED
    f_type = CRIMSON
    initialise_optimisation(length, width, num_dispensers, f_type)

# bone meal efficiency can be converted to wart block efficiency and defined as the amount of wart
# blocks your farm's blast chamber is able to harvest per fungi grown, thus bone meal efficiency
# can be tuned and inputted using a slider and optimal layouts can factor in that bm/wb efficiency

# after calculating the most optimal positions to put the dispensers for crimson
# it should generate a list of all permutations of the order, 4 rotations, and 2 mirrors and then calculate which set of new orientations is best out of those for warped
# further, out of the entire set, it should compare the difference between the worst possible ordering of those dispensers and the
# best to see if it's worth worrying about activation order