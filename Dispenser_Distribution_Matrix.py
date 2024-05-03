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

def compute_weights(offsets, kn1):
    """Compute the dispenser distribution weighting for a given dispenser placement."""
    r_hk = r(offsets[0][kn1])
    r_vk = r(offsets[1][kn1])
    abs_hk = abs(offsets[0][kn1])
    abs_vk = abs(offsets[1][kn1])
        
    vertical_shift = mpow(R, r_vk) @ mpow(S, abs_vk) @ mpow(R, r_vk)
    horizontal_shift = mpow(R, r_hk) @ mpow(S, abs_hk) @ mpow(R, r_hk)
    
    return vertical_shift @ DISP_DIST @ horizontal_shift

def sum_foliage_distribution(offsets):
    """Sum the foliage distribution for a given set of offsets."""
    n = len(offsets) // 2
    fc = 0
    for k in range(1, n + 1):
        inner_sum = 0
        for j in range(1, k):
            disp_x = offsets[0][k-1][k-1]
            disp_y = offsets[1][k-1][k-1]
            inner_sum += compute_weights(R, S, offsets[j-1])[disp_x][disp_y]
        fc += (1 - inner_sum) * compute_weights(R, S, offsets, k-1)
    return fc

if __name__ == '__main__':
    offsets = [[2], [2]]
    result = sum_foliage_distribution(offsets)
    print("Sum:", np.sum(result))
    print("Distribution:", result)