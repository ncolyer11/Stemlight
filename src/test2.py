from random import randint
from time import time

num_cycles = 150000000
start_time = time()
total_E = 0
for c in range(num_cycles):
    foliage_F = 0
    foliage_E = 0
    # 2 rounds for normal foliage, and then for sprouts
    # Go through 9 cycles in total for each round
    for _ in range(18):
        (x, y) = (randint(0, 2) - randint(0, 2), randint(0, 2) - randint(0, 2))
        if (x, y) == (0, 0):
            foliage_F = 1
        elif (x, y) == (1, 0):
            foliage_E = 1

    # If there's air above the dispenser and the 1/8 chance succeeds
    if not foliage_F and randint(0, 7) == 0:
        for _ in range(9):
            (x, y), z = (randint(-3, 3), randint(-3, 3)), randint(-1, 1)
            if (x, y) == (1, 0) and z in [0, 1] and not foliage_E:
                total_E += 1
                break
    
    if c % (num_cycles // 100) == 0 and c != 0:
        print(f"Values at cycle {c}:\n\t{18e3 * total_E / c:.4f}")
P_E_round2 = total_E / num_cycles

# This currently replicates results from carpet simulations in game
# Desmos math agrees only with region F, and overestimates region E and presumably the rest
print(f"Probability of a twisting vine generating at E: {18e3 * P_E_round2:.4f}")
print(f"Time simulated: {num_cycles / (5 * 60):.3f} minutes")
print(f"Time taken: {(time() - start_time):.3f} seconds")
