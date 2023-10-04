# a program that finds the optimal position to place n dispensers on a custom size grid of nylium
# (generally less than 5x5)
# TO-DO: add GUI, use a horizontal and vertical slider that are n + 1 long adjacent to a grid of n x n checkboxes
# where the order you click the checkboxes is the order the dispensers fire in (add reset selection button)
# label input for number of cycles
# sidebar with a list of all dispensers and another adjacent checkbox to select whether or not the block above the
# dispenser is cleared every cycle

# USE SCHEMATIC OF NYLIUM + DISPENSER INPUT AND GUI LIKE LAYOUT RATES CALCULATOR

width = int(input("Enter Width of Nylium Grid: "))
length = int(input("Enter Length of Nylium Grid: "))
dispensers = int(input("Enter Amount of Dispensers: "))

coordinates = []
for i in range(dispensers):
    while True:
        x = int(input(f'Enter x-Offset from NW corner for dispenser {i + 1}: '))
        y = int(input(f'Enter y-Offset from NW corner for dispenser {i + 1}: '))
        if 0 <= x < width and 0 <= y < length:
            coordinates.append((x, y))
            break
        else:
            print(f'Error: The offset values must be within the bounds of the {width}x{length} grid.')

# Create 2D array of given size and initialize all elements to 0
nyliumGrid = [[0 for i in range(length)] for j in range(width)]
def selection_chance(x1, y1):
    x2 = 3 - abs(x1)
    y2 = 3 - abs(y1)
    P_block = x2 * y2 / 81
    P_block = 0 if x2 < 0 or y2 < 0 else P_block
    P = 0
    for k in range(1, 10):
        P += (1 - P_block) ** (9 - k)
    return P * P_block * 11 / 99  # 11/99 for crimson and 13/100 for warped

bonemeal_used = 0
for i in range(dispensers):
    # chance of dispenser being able to fire from lack of foliage above it
    C = (1 - nyliumGrid[coordinates[i][0]][coordinates[i][1]])
    bonemeal_used += C
    for x in range(width):
        for y in range(length):
            S = selection_chance(x - coordinates[i][0], y - coordinates[i][1])
            B = nyliumGrid[x][y] * C * S
            nyliumGrid[x][y] = round(nyliumGrid[x][y] + C * S - B, 5)

# Print the resulting array
for i in range(width):
    print(" ".join(["{:<8}".format(nyliumGrid[i][j]) for j in range(length)]))

total = 0
for x in range(width):
    for y in range(length):
        total += nyliumGrid[x][y]


print(f'total items: {total}')
print(f'crimson fungi: {total}')
print(f'bonemeal_used: {bonemeal_used}')

if dispensers > 0:
    print("For dispensers in the following order, placed at:")
    blockGrid = [[0 for i in range(length)] for j in range(width)]
    dis = 1
    for i in range(dispensers):
        x = coordinates[i][0]
        y = coordinates[i][1]
        blockGrid[x][y] = dis
        dis += 1

    for x in range(width):
        for y in range(length):
            if blockGrid[x][y] != 0:
                print(f'[{blockGrid[x][y]}]', end='')
            else:
                print('[ ]', end='')
        print('\n', end='')
