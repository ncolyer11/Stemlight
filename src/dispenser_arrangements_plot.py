import numpy as np
import itertools
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d import Axes3D
import math
import src.Assets.constants as const

WARPED = 0
CRIMSON = 1

# Selection cache
selection_cache = np.array([
    [0.6535605838853813, 0.4997510328685407, 0.28798973593014715],
    [0.4997510328685407, 0.3660553272880777, 0.20149313967509574],
    [0.28798973593014715, 0.20149313967509574, 0.10577931226910778],
])

class LayoutInfo:
    def __init__(self, num_disps, length, width, disp_layout):
        self.num_disps = num_disps
        self.length = length
        self.width = width
        self.disp_layout = disp_layout
        # self.num_cycles = num_cycles
        # self.blocked_blocks = blocked_blocks

def main():
    L = LayoutInfo(
        num_disps=int(input("Enter the number of dispensers: ")),
        length=5,
        width=5,
        disp_layout=None,
        # num_cycles=1,
        # blocked_blocks=None
    )
    
    big_size = 5 ** (L.num_disps)
    print(f"big_size: {big_size}")
    data = np.random.randn(math.factorial(L.num_disps), big_size, big_size)
    data = np.zeros((math.factorial(L.num_disps), big_size, big_size))
    layouts = generate_dispenser_positions(L.num_disps)
    print(f"compare shape: {data.shape}, {layouts.shape}")  
    for perm_idx, layout in enumerate(layouts):
        print(f"perm_idx: {perm_idx}")
        for layout_idx, disp_pos in enumerate(layout):
            # Calculate the row and column index for the current 5x5 chunk
            row = (layout_idx // (big_size))
            col = (layout_idx % (big_size))
            
            # Compute the 5x5 array using the warped_calc_fung_dist function
            chunk = warped_calc_fung_dist(5, 5, disp_pos)
            
            # Place the 5x5 array in the correct position in the large array
            print(f"layout_idx: {layout_idx}, row: {row}, col: {col}")  
            data[perm_idx][row:row + 5, col:col + 5] = chunk
    
    print(f"max: {np.max(data)}")
    n_dim_plot_disps(data)

def warped_calc_fung_dist(length, width, disp_layout):
    # 2D arrays for storing distribution of all the foliage as well as the desired fungi
    foliage_grid = np.zeros((width, length))
    des_fungi_grid = np.zeros((width, length))

    x, y = np.ogrid[:width, :length]
    for (disp_x, disp_y) in disp_layout:
        x1 = np.abs(x - disp_x).astype(int)
        y1 = np.abs(y - disp_y).astype(int)
        sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                            selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])
        
        disp_chance = (1 - foliage_grid[disp_x, disp_y])
        foliage_chance = sel_chance * disp_chance

        des_fungi_grid += (1 - foliage_grid) * foliage_chance * const.WARP_FUNG_CHANCE
        
        foliage_grid += (1 - foliage_grid) * foliage_chance
        
        # As it's warped nylium, generate sprouts
        sprouts_chance = (1 - foliage_grid) * foliage_chance
        foliage_grid += sprouts_chance

    return np.sum(des_fungi_grid)

def generate_dispenser_positions(n):
    # Generate all row, col positions on a 5x5 grid
    grid_positions = [(i, j) for i in range(5) for j in range(5)]
    print(f"grid_positions: {grid_positions}\n")
    
    # Generate all permutations of the n dispensers (ordering)
    dispenser_permutations = list(itertools.permutations(range(n)))
    print(f"dispenser_permutations: {dispenser_permutations}\n")
    
    # Generate all possible positions (allowing overlap) for n dispensers on the grid
    # There should be 5^(n+1) combinations of positions
    position_combinations = list(itertools.product(grid_positions, repeat=n))[:5**(n+2)]
    print(f"position_combinations: {position_combinations} (total: {len(position_combinations)})\n")  # Showing a subset for brevity
    
    # Initialize the result array with shape (n!, 5^(n+1), n, 2)
    result = np.zeros((len(dispenser_permutations), len(position_combinations), n, 2), dtype=int)
    
    # Fill in the result array
    for perm_idx, perm in enumerate(dispenser_permutations):
        for pos_idx, positions in enumerate(position_combinations):
            # Assign positions for each dispenser according to the current permutation
            for disp_idx, dispenser_id in enumerate(perm):
                result[perm_idx, pos_idx, dispenser_id] = positions[disp_idx]
    
    return result

def n_dim_plot_disps(data):
    # Initialize figure and 3D axis
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    
    # Create the initial bar plot
    x = np.arange(data.shape[1])
    y = np.arange(data.shape[2])
    X, Y = np.meshgrid(x, y)
    Z = data[0]  # Start with the first permutation
    
    # Flatten the arrays for bar3d
    xpos = X.flatten()
    ypos = Y.flatten()
    zpos = np.zeros_like(xpos)
    dx = dy = 0.8  # Bar width (slightly less than 1 to avoid gaps)
    dz = Z.flatten()
    
    # Create color mapping
    norm = plt.Normalize(dz.min(), dz.max())
    colors = plt.cm.viridis(norm(dz))
    
    # Create the 3D bar plot
    bars = ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color=colors, zsort='average')
    
    # Add colorbar
    m = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=norm)
    m.set_array(dz)
    fig.colorbar(m, ax=ax, shrink=0.5, aspect=5)
    # Create a slider for permutation selection
    ax_slider = plt.axes([0.2, 0.02, 0.6, 0.03], facecolor='lightgoldenrodyellow')
    slider = Slider(ax_slider, 'Permutation', 1, data.shape[0], valinit=1, valstep=1)
    permutation_index = int(slider.val) - 1
    
    ax.set_title(f"(1+2*N+N!) Dimensional (projected down) plot\n"
                 f"for total desired fungi for N dispensers{permutation_index + 1}")
    ax.set_xlabel("Every 5^n is the x-coord of dispenser n")
    ax.set_ylabel("Every 5^n is the z-coord of dispenser n")
    ax.set_zlabel("Avg Fungi Generated")
    
    
    # Update function to change the bar plot when slider value changes
    def update(val):
        permutation_index = int(slider.val) - 1
        ax.clear()  # Clear the existing plot
        
        # Update Z data
        dz = data[permutation_index].flatten()
        
        # Update colors based on new values
        colors = plt.cm.viridis(norm(dz))
        
        # Create new bars
        ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color=colors, zsort='average')
        
        ax.set_title(f"(1+2*N+N!) Dimensional (projected down) plot\n"
                     f"for total desired fungi for N dispensers{permutation_index + 1}")
        ax.set_xlabel("Every 5^n is the x-coord of dispenser n")
        ax.set_ylabel("Every 5^n is the z-coord of dispenser n")
        ax.set_zlabel("Avg Fungi Generated")
        plt.draw()
    
    # Attach update function to slider
    slider.on_changed(update)
    plt.show()

if __name__ == "__main__":
    main()