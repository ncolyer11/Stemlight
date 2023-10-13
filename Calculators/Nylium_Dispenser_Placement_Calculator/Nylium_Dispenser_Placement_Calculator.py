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

while True:
    disp_coordinates = []
    fungi = input("Enter Nylium Type: ").lower().strip()
    # shorcut for 1 centred dispenser on a 5x5 platform of nylium
    if fungi in {"d", "default", "d2", "default2"}:
        if fungi in {"d", "default"}:
            fungi = 0
            fungi_weight = 13/100  # 13/100 for warped
        else:
            fungi = 1
            fungi_weight = 11/99  # 11/99 for crimson
        width = 5
        length = 5
        dispensers = 1
        disp_coordinates.append((2, 2))
        break
    elif fungi in {"blue", "b", "warped", "w", "warp"}:
        fungi = 0  # warped
    elif fungi in {"red", "r", "crimson", "c", "crim"}:
        fungi = 1  # crimson
    else:
        print("Error: Please enter a valid nylium type")
        exit(1)
    if fungi == 0:
        fungi_weight = 13/100  # 13/100 for warped
    else:
        fungi_weight = 11/99  # 11/99 for crimson

    length = int(input("Enter Length of Nylium Grid: "))
    width = int(input("Enter Width of Nylium Grid: "))
    dispensers = int(input("Enter Amount of Dispensers: "))

    for i in range(dispensers):
        while True:
            x = int(input(f'Enter x-Offset from NW corner for dispenser {i + 1}: '))
            y = int(input(f'Enter y-Offset from NW corner for dispenser {i + 1}: '))
            if 0 <= x < width and 0 <= y < length:
                disp_coordinates.append((x, y))
                break
            else:
                print(f'Error: The offset values must be within the bounds of the {width}x{length} grid.')
    break

# Create 2D array storing total plant growth chance of given size and initialize all elements to 0
foliage_grid = np.zeros((width, length))
# Create 2D array storing desired fungi growth chance of given size and initialize all elements to 0
des_fungi_grid = np.zeros((width, length))

def selection_chance(x1, y1):
    x2 = 3 - abs(x1)
    y2 = 3 - abs(y1)
    P_block = x2 * y2 / 81
    P_block = 0 if x2 < 0 or y2 < 0 else P_block
    P = 0
    for k in range(1, 10):
        P += (1 - P_block) ** (9 - k)
    return P * P_block

bonemeal_used = 0
for i in range(dispensers):
    # chance of dispenser being able to fire from lack of foliage above it
    dispenser_x = disp_coordinates[i][0]
    dispenser_y = disp_coordinates[i][1]
    dispenser_fail_chance = (1 - foliage_grid[dispenser_x][dispenser_y])
    bonemeal_used += dispenser_fail_chance
    for x, y in iter.product(range(width), range(length)):
        # selection_chance(offset from dispenser posX, offset from dispenser posY)
        # the chance of a new foliage generating at the given offset pos
        foliage_chance = selection_chance(x - dispenser_x, y - dispenser_y)
        # the chance of a desired fungi generating at the given offset pos
        des_fungi_chance = foliage_chance * fungi_weight
        # P(fungi) = P(dispenser not obstructred) * P(desired fungi being selected) * P(offset block not blocked)
        des_fungi_grid[x][y] += dispenser_fail_chance * des_fungi_chance * (1 - foliage_grid[x][y])
        foliage_grid[x][y] += dispenser_fail_chance * foliage_chance * (1 - foliage_grid[x][y])
        # warped nylium has another 9 cycles to generate sprouts
        if fungi == 0:
            foliage_chance = selection_chance(x - dispenser_x, y - dispenser_y)
            foliage_grid[x][y] += dispenser_fail_chance * foliage_chance * (1 - foliage_grid[x][y])
    # only enable for testing when clearing centre nylium with a piston for a 1 dispenser centred on a 5x5 platform
    # if dispensers > 1:
    #     foliage_grid[2][2] = 0
    #     des_fungi_grid[2][2] = 0

# print the resulting fungi gen chance values for each block in the nylium grid
for i in range(width):
    print(" ".join(["{:<8}".format(round(des_fungi_grid[i][j], 5)) for j in range(length)]))

total_fungi = 0
total_plants = 0
for x, y in iter.product(range(width), range(length)):
    total_fungi += des_fungi_grid[x][y]
    total_plants += foliage_grid[x][y]

print(f'total plants: {round(total_plants, 5)}')
if fungi == 0:
    print(f'warped fungi: {round(total_fungi, 5)}')
else:
    print(f'crimson fungi: {round(total_fungi, 5)}')
print(f'bonemeal_used: {round(bonemeal_used, 5)}')

if dispensers > 0:
    print("For dispensers in the following order, placed at:")
    blockGrid = np.zeros((length, width), dtype=int)
    dis = 1
    for i in range(dispensers):
        x = disp_coordinates[i][0]
        y = disp_coordinates[i][1]
        blockGrid[x][y] = dis
        dis += 1

    for x, y in iter.product(range(length), range(width)):
        if blockGrid[x][y] != 0:
            print(f'[{blockGrid[x][y]}]', end='')
        else:
            print('[ ]', end='')
        if y == length - 1:
            print('\n', end='')
