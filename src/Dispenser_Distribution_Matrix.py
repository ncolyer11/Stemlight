import numpy as np

# Selection probabilities for blocks offset around a centred dispenser on a 5x5 grid of nylium
SP = [
    0.10577931226910778, 0.20149313967509574,
    0.28798973593014715, 0.3660553272880777,
    0.4997510328685407, 0.6535605838853813
]
DISP_DIST = np.array([
    [SP[0], SP[1], SP[2], SP[1], SP[0]],
    [SP[1], SP[3], SP[4], SP[3], SP[1]],
    [SP[2], SP[4], SP[5], SP[4], SP[2]],
    [SP[1], SP[3], SP[4], SP[3], SP[1]],
    [SP[0], SP[1], SP[2], SP[1], SP[0]],
])
# Shift matrix
S = np.array([
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0]
])
# Reflection matrix
R = np.array([
    [0, 0, 0, 0, 1],
    [0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0],
    [0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0]
])
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

def calculate_disp_fire_chance(k, offsets):
    """Calculate the chance of an air block being above a given dispenser."""
    fire_chance = 1
    for j in range(1, k):
        h_k = offsets[k-1][0]
        v_k = offsets[k-1][1]
        fire_chance -= compute_weights(offsets[j-1])[h_k][v_k]
    return fire_chance

def calculate_empty_chance_matrix(k, offsets):
    """Calculate the chance of there being an air block above a given offset on the nylium grid"""
    empty_chance = np.ones((5, 5))
    for j in range(1, k):
        empty_chance -= compute_weights(offsets[j-1])
    return empty_chance

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
    offsets = [[0,0], [1,1]]
    result = foliage_distribution(offsets)
    print("Offsets: \n", offsets)
    print("Distribution: \n", result)
    print("Sum:", np.sum(result))