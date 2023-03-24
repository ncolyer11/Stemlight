# a program that finds the optimal position to place n dispensers on a custom size grid of nylium
# (generally less than 5x5)


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
    P = x2 * y2
    P = 0 if x2 < 0 or y2 < 0 else P
    return 1 - (1 - P / 81) ** 9
    # return P


for i in range(dispensers):
    # chance of dispenser being able to fire from lack of foliage above it
    C = (1 - nyliumGrid[coordinates[i][1]][coordinates[i][0]])
    for y in range(length):
        for x in range(width):
            S = selection_chance(x - coordinates[i][0], y - coordinates[i][1])
            B = nyliumGrid[y][x] * C * S
            nyliumGrid[y][x] = round(nyliumGrid[y][x] + C * S - B, 5)

# Print the resulting array
for i in range(width):
    print(" ".join(["{:<8}".format(nyliumGrid[i][j]) for j in range(length)]))

total = 0
for x in range(width):
    for y in range(length):
        total += nyliumGrid[y][x]

print(f'total: {total}')

print("For dispensers in the following order, placed at:")
blockGrid = [[0 for i in range(length)] for j in range(width)]
dis = 1
for i in range(dispensers):
    x = coordinates[i][1]
    y = coordinates[i][0]
    blockGrid[x][y] = dis
    dis += 1

for x in range(width):
    for y in range(length):
        if blockGrid[x][y] != 0:
            print(f'[{blockGrid[x][y]}]', end='')
        else:
            print('[ ]', end='')
    print('\n', end='')
