# a program that finds the optimal position to place n dispensers on a custom size grid of nylium
# (generally less than 5x5)
# TO-DO: add GUI, use a horizontal and vertical slider that are n + 1 long adjacent to a grid of n x n checkboxes
# where the order you click the checkboxes is the order the dispensers fire in (add reset selection button)
# label input for number of cycles
# sidebar with a list of all dispensers and hover over a dispenser to tell u how much bm it uses per cycle

import numpy as np
import itertools as iter
import questionary


from Assets import constants as const

DP_VAL = 5

def get_size_input(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                raise ValueError(f"Error: Please enter a positive integer for {prompt.split()[1].lower()}.")
            return value
        except ValueError:
            print(f"Error: Please enter a positive integer for {prompt.split()[1].lower()}.")

def display_nylium_platform(width, length):
    print("Here is your nylium platform:")
    for i in range(width):
        for j in range(length):
            print("[ ]", end="")
        print("")

def get_num_dispensers():
    while True:
        try:
            dispensers = int(input("Enter Amount of Dispensers: "))
            break
        except ValueError:
            print("Error: Please enter a positive integer for dispensers.")
    return dispensers

def get_dispenser_coords(dispensers, length, width):
    coords = []
    for i in range(dispensers):
        x_offset = 0
        y_offset = 0
        for coord_name in ['x', 'y']:
            while True:
                try:
                    offset = int(input(f'Enter {coord_name}-offset from NW corner for dispenser {i + 1}: '))
                    if 0 <= offset < (length if coord_name == 'x' else width):
                        break
                    print(f'Error: The {coord_name}-offset must be a positive integer less than {length if coord_name == "x" else width}.')
                except ValueError:
                    print(f'Error: Please enter a positive integer for {coord_name}-offset.')
                    continue

            if coord_name == 'y':
                y_offset = offset
            else:
                x_offset = offset
        coords.append((y_offset, x_offset))

    return coords         

def selection_chance(x1, y1):
    x2 = const.FUNG_SPREAD_RAD - abs(x1)
    y2 = const.FUNG_SPREAD_RAD - abs(y1)
    P_block = x2 * y2 / (const.FUNG_SPREAD_RAD ** 4)
    P_block = 0 if x2 < 0 or y2 < 0 else P_block
    P = 0
    for k in range(1, const.FUNG_SPREAD_RAD ** 2 + 1):
        P += (1 - P_block) ** (const.FUNG_SPREAD_RAD ** 2 - k)
    return P * P_block   


while True:
    default = 0
    while True:
        disp_coordinates = []
        fungi = input("Enter Nylium Type: ").lower().strip()
        # shorcut for 1 centred dispenser on a 5x5 platform of nylium (' ' for warped and '2' for crimson)
        if fungi in {"d", "default", "d2", "default2"}:
            if fungi in {"d", "default"}:
                fungi = 0
                fungi_weight = const.WARP_FUNG_CHANCE  # 13/100 for warped
            else:
                fungi = 1
                fungi_weight = const.CRMS_FUNG_CHANCE  # 11/99 for crimson
            width = const.FUNG_SPREAD_DIA
            length = const.FUNG_SPREAD_DIA
            dispensers = 1
            disp_coordinates.append((const.FUNG_SPREAD_RAD - 1, const.FUNG_SPREAD_RAD - 1))
            default = 1
            break
        elif fungi in const.WARP_OPTIONS:
            fungi = 0  # warped
            fungi_weight = const.WARP_FUNG_CHANCE
        elif fungi in const.CRMS_OPTIONS:
            fungi = 1  # crimson
            fungi_weight = const.CRMS_FUNG_CHANCE
        else:
            print("Error: Please enter a valid nylium type.")
            continue
        break

    if default == 0:
        length = get_size_input("Enter Length of Nylium Grid: ")
        width = get_size_input("Enter Width of Nylium Grid: ")
        display_nylium_platform(width, length)
        dispensers = get_num_dispensers()
        disp_coordinates = get_dispenser_coords(dispensers, length, width)
                    
    # Create 2D array storing total plant growth chance of given size and initialize all elements to 0
    foliage_grid = np.zeros((width, length))
    # Create 2D array storing desired fungi growth chance of given size and initialize all elements to 0
    des_fungi_grid = np.zeros((width, length))

    bm_for_prod = 0
    for i in range(dispensers):
        # chance of dispenser being able to fire from lack of foliage above it
        dispenser_x = disp_coordinates[i][0]
        dispenser_y = disp_coordinates[i][1]
        dispenser_bm_chance = (1 - foliage_grid[dispenser_x][dispenser_y])
        bm_for_prod += dispenser_bm_chance

        for x, y in iter.product(range(width), range(length)):
            # selection_chance(offset from dispenser posX, offset from dispenser posY)
            # the chance of a new foliage generating at the given offset pos
            foliage_chance = selection_chance(x - dispenser_x, y - dispenser_y)
            # the chance of a desired fungi generating at the given offset pos
            des_fungi_chance = foliage_chance * fungi_weight
            # P(fungi) = P(dispenser not obstructred) * P(desired fungi being selected) * P(offset block not blocked)
            des_fungi_grid[x][y] += dispenser_bm_chance * des_fungi_chance * (1 - foliage_grid[x][y])
            foliage_grid[x][y] += dispenser_bm_chance * foliage_chance * (1 - foliage_grid[x][y])
            # warped nylium has another 9 cycles to generate sprouts
            if fungi == 0:
                foliage_chance = selection_chance(x - dispenser_x, y - dispenser_y)
                foliage_grid[x][y] += dispenser_bm_chance * foliage_chance * (1 - foliage_grid[x][y])
        # only enable for testing when clearing centre nylium with a piston for a 1 dispenser centred on a 5x5 platform
        # if dispensers > 1:
        #     foliage_grid[2][2] = 0
        #     des_fungi_grid[2][2] = 0

    # print the resulting fungi gen chance values for each block in the nylium grid
    for i in range(width):
        print(" ".join(["{:<8}".format(round(des_fungi_grid[i][j], DP_VAL)) for j in range(length)]))

    total_fungi = 0
    total_plants = 0
    for x, y in iter.product(range(width), range(length)):
        total_fungi += des_fungi_grid[x][y]
        total_plants += foliage_grid[x][y]
    bm_for_grow = const.AVG_BM_TO_GROW_FUNG * total_fungi
    bm_total = bm_for_prod + bm_for_grow

    print(f'Total plants: {round(total_plants, DP_VAL)}')
    if fungi == 0:
        print(f'Warped fungi: {round(total_fungi, DP_VAL)}')
    else:
        print(f'Crimson fungi: {round(total_fungi, DP_VAL)}')
    print(f'Bone meal used per cycle (to produce + to grow):\n'
            f'{round(bm_for_prod, DP_VAL)} + {round(bm_for_grow, DP_VAL)} = '
            f'{round(bm_total, DP_VAL)}')


    if dispensers > 0:
        print("For dispensers in the following order, placed at:")
        blockGrid = np.zeros((width, length), dtype=int)
        dis = 1
        for i in range(dispensers):
            x = disp_coordinates[i][0]
            y = disp_coordinates[i][1]
            blockGrid[x][y] = dis
            dis += 1

        for x, y in iter.product(range(width), range(length)):
            if blockGrid[x][y] != 0:
                print(f'[{blockGrid[x][y]}]', end='')
            else:
                print('[ ]', end='')
            if y == length - 1:
                print('\n', end='')
    
    if not questionary.confirm("Run Again?").ask():
        break
