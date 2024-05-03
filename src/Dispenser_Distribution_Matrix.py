import numpy as np

from Assets.helpers import create_dispenser_distribution

# Nylium Platform/Grid Size
SIZE = 5
# Distribution describing foliage spread after bone-mealing the centre nylium on a 5x5 platform
DISP_DIST = create_dispenser_distribution(SIZE)
# Shift matrix
S = np.eye(SIZE, k=1)
# Reflection matrix
R = np.fliplr(np.eye(SIZE))
# Define shorthand for exponentiating a matrix
mpow = np.linalg.matrix_power

def r(x):
    """Returns 1 if x is negative, 0 otherwise."""
    return 1 if x < 0 else 0
    # Math version: (this is a pure function so can get away with using the above ternary shortcut)
    # return (1 - np.sign(x)) // 2
    
def compute_weights(offsets):
    """Compute the dispenser distribution weighting for a given dispenser placement."""
    r_h = r(offsets[0])
    r_v = r(offsets[1])
    abs_h = abs(offsets[0])
    abs_v = abs(offsets[1])
        
    vertical_shift = mpow(R, r_v) @ mpow(S, abs_v) @ mpow(R, r_v)
    horizontal_shift = mpow(R, r_h) @ mpow(S, abs_h) @ mpow(R, r_h)
    
    return vertical_shift @ DISP_DIST @ horizontal_shift

def calculate_empty_chance_matrix(k, offsets):
    """Calculate the chance of there being an air block above a given offset on the nylium grid"""
    blocked_chance = np.zeros((5, 5))
    for j in range(1, k):
        blocked_chance += compute_weights(offsets[j-1])
    return 1 - blocked_chance

def calculate_disp_fire_chance(k, offsets):
    """Calculate the chance of an air block being above a given dispenser."""
    blocked_chance = 0
    for j in range(1, k):
        h_k = offsets[k-1][0]
        v_k = offsets[k-1][1]
        blocked_chance += compute_weights(offsets[j-1])[2 + v_k][2 + h_k]
    return 1 - blocked_chance

def foliage_distribution(offsets):
    """Sum the foliage distribution on a grid of nylium for a given set of dispenser offsets."""
    n = len(offsets)
    distribution = 0
    for k in range(1, n+1):
        empty_chance = calculate_empty_chance_matrix(k, offsets)
        disp_fire_chance = calculate_disp_fire_chance(k, offsets)
        distribution += disp_fire_chance * empty_chance * compute_weights(offsets[k-1])
    return np.sum(distribution)

if __name__ == '__main__':
    offsets = [[-2, 0], [1, 0], [0, -2]]
    result = foliage_distribution(offsets)
    print("Offsets: \n", offsets)
    print("Distribution: \n", result)
    print("Sum:", np.sum(result))