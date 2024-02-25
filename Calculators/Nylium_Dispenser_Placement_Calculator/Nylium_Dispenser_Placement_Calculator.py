# a program that finds the optimal position to place n dispensers on a custom size grid of nylium
# (generally less than 5x5)
# TO-DO: add GUI, use a horizontal and vertical slider that are n + 1 long adjacent to a grid of n x n checkboxes
# where the order you click the checkboxes is the order the dispensers fire in (add reset selection button)
# label input for number of cycles
# sidebar with a list of all dispensers and another adjacent checkbox to select whether or not the block above the
# dispenser is cleared every cycle

# USE SCHEMATIC OF NYLIUM + DISPENSER INPUT AND GUI LIKE LAYOUT RATES CALCULATOR

import numpy as np
import itertools as iter

from Assets import constants as const

DP_VAL = 5

while True:
    disp_coordinates = []
    fungi = input("Enter Nylium Type: ").lower().strip()
    # shorcut for 1 centred dispenser on a 5x5 platform of nylium
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
        clearing = 0
        break
    elif fungi in const.WARP_OPTIONS:
        fungi = 0  # warped
    elif fungi in const.CRMS_OPTIONS:
        fungi = 1  # crimson
    else:
        print("Error: Please enter a valid nylium type")
        exit(1)
    if fungi == 0:
        fungi_weight = const.WARP_FUNG_CHANCE  # 13/100 for warped
    else:
        fungi_weight = const.CRMS_FUNG_CHANCE  # 11/99 for crimson

    length = int(input("Enter Length of Nylium Grid: "))
    width = int(input("Enter Width of Nylium Grid: "))

    # Show user current sized grid
    print("Here is your nylium platform:")
    for i in range(width):
        for j in range(length):
            print("[ ]", end="")
        print("")

    dispensers = int(input("Enter Amount of Dispensers: "))

    for i in range(dispensers):
        while True:
            y = int(input(f'Enter x-Offset from NW corner for dispenser {i + 1}: '))
            x = int(input(f'Enter y-Offset from NW corner for dispenser {i + 1}: '))
            if 0 <= x < width and 0 <= y < length:
                disp_coordinates.append((x, y))
                break
            else:
                print(f'Error: The offset values must be within the bounds of the {width}x{length} grid.')

    clearing = input("Enter if clearing above dispensers: ").lower().strip()
    if clearing in {"y", "yes", "1", "true"}:
        clearing = 1
    else:
        clearing = 0
    break


# Create 2D array storing total plant growth chance of given size and initialize all elements to 0
foliage_grid = np.zeros((width, length))
# Create 2D array storing desired fungi growth chance of given size and initialize all elements to 0
des_fungi_grid = np.zeros((width, length))

def selection_chance(x1, y1):
    x2 = const.FUNG_SPREAD_RAD - abs(x1)
    y2 = const.FUNG_SPREAD_RAD - abs(y1)
    P_block = x2 * y2 / (const.FUNG_SPREAD_RAD ** 4)
    P_block = 0 if x2 < 0 or y2 < 0 else P_block
    P = 0
    for k in range(1, const.FUNG_SPREAD_RAD ** 2 + 1):
        P += (1 - P_block) ** (const.FUNG_SPREAD_RAD ** 2 - k)
    return P * P_block

bonemeal_used = 0
for i in range(dispensers):
    # chance of dispenser being able to fire from lack of foliage above it
    dispenser_x = disp_coordinates[i][0]
    dispenser_y = disp_coordinates[i][1]
    dispenser_bm_chance = (1 - foliage_grid[dispenser_x][dispenser_y])
    if clearing == 1:
        dispenser_bm_chance = 1 # as above block is always cleared
    bonemeal_used += dispenser_bm_chance

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

print(f'total plants: {round(total_plants, DP_VAL)}')
if fungi == 0:
    print(f'warped fungi: {round(total_fungi, DP_VAL)}')
else:
    print(f'crimson fungi: {round(total_fungi, DP_VAL)}')
print(f'bonemeal_used: {round(bonemeal_used, DP_VAL)}')

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
