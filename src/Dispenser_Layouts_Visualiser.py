import os
import time
import numpy as np
import itertools
import matplotlib.pyplot as plt
import pandas as pd
import src.Assets.constants as const
import plotly.graph_objects as go

WARPED = 0
CRIMSON = 1
MPL_FIG_RATIO = 2.2
LW_BASE_WDTH = 0.5

# Selection cache
selection_cache = np.array([
    [0.6535605838853813, 0.4997510328685407, 0.28798973593014715],
    [0.4997510328685407, 0.3660553272880777, 0.20149313967509574],
    [0.28798973593014715, 0.20149313967509574, 0.10577931226910778],
])

def command_loop():
    commands = {
        'p': plot_from_csv,
        'i': export_plot_as_2d_image,
        's': simulate_and_plot_custom_layout,
        'r': run_all_sims_and_export,
        'q': lambda: print("Quitting...")
    }

    while True:
        command = input("Enter a command: ")
        if command == 'q':
            commands[command]()
            break
        elif command in commands:
            commands[command]()
        else:
            print("Invalid command. Please try again.")

#########################
### COMMAND FUNCTIONS ###
#########################
def plot_from_csv():
    """
    Reads data from a CSV file and plots it in 2D or 3D.
    
    Parameters:
    num_dispensers (int): The number of dispensers.
    plot_type (str): The type of plot ('2' or '3').
    """
    num_disps = int(input("Enter the number of dispensers: "))
    plot_type = input("Enter plot type (2/3): ")
    

    print("Reading and plotting from CSV file...")
    file_name = f"{num_disps}_dispenser{'s' if num_disps > 1 else ''}_5x5.csv"
    file_path = os.path.join('disp_optimisation', file_name)
    data = pd.read_csv(file_path).values
    
    if plot_type == '3':
        n_dim_plot_disps_3d_plotly(data, num_disps)
    else:
        n_dim_plot_disps_2d(data, num_disps)

def export_plot_as_2d_image():
    """
    Generates a 2D plot from a CSV file and saves it as an image.
    """
    num_dispensers = int(input("Enter the number of dispensers: "))
    file_name = f"{num_dispensers}_dispenser{'s' if num_dispensers > 1 else ''}_5x5.csv"
    file_path = os.path.join('disp_optimisation', file_name)
    data = pd.read_csv(file_path).values
    
    # dpi = int(input("Enter the DPI for the image: "))
    dpi = max(400, int(MPL_FIG_RATIO * 5 ** num_dispensers / 10))
    
    file_name = f"{num_dispensers}_dispenser{'s' if num_dispensers > 1 else ''}_5x5 dpi={dpi}.png"
    file_path = os.path.join(f'disp_optimisation', file_name)
    n_dim_plot_disps_2d(data, num_dispensers, dpi, True)
    
    print(f"Saved in {file_path}")
   
def simulate_and_plot_custom_layout():
    """
    Simulates and plots a custom layout of dispensers in either 2D or 3D.
    """
    num_disps = int(input("Enter the number of dispensers: "))
    plot_type = input("Enter plot type (2/3): ")
    
    print("Plotting custom layout...")
    big_size = 5 ** (num_disps)
    print(f"big_size: {big_size}")


    data = np.zeros((big_size, big_size))
    layouts = generate_dispenser_positions(num_disps)
    powers_of_5 = 5 ** np.arange(num_disps)

    for layout in layouts:
        # Convert the base 5 coordinates to row and column indices
        row_vals, col_vals = layout.T

        row = np.sum(row_vals * powers_of_5)
        col = np.sum(col_vals * powers_of_5)
        
        des_fungi = fast_calc_fung_dist(5, 5, CRIMSON, layout)
        data[row, col] = des_fungi
    
    print(f"max: {np.max(data)}")
    if plot_type == '3':
        n_dim_plot_disps_3d_plotly(data, num_disps)
        # n_dim_plot_disps_3d(data, num_disps)
    else:
        n_dim_plot_disps_2d(data, num_disps)

def run_all_sims_and_export():
    """
    Calculates 'data' and exports to a different csv file each time for increasingly larger 
    dispenser counts.
    """
    max_disp_count = int(input("Enter the maximum number of dispensers to simulate unto: "))
    os.makedirs('disp_optimisation', exist_ok=True)
    f_type = int(input("Enter the fungus type (0 for warped, 1 for crimson): "))
    f_name = 'warped' if f_type == WARPED else 'crimson'
    for i in range(1, max_disp_count + 1):
        start_time = time.time_ns()
        big_size = 5 ** i
        edge = big_size - 1
        data = np.zeros((big_size, big_size))
        layouts = generate_dispenser_positions(i)
        powers_of_5 = 5 ** np.arange(i)
        for layout in layouts:
            # Convert the base 5 coordinates to row and column indices
            row_vals, col_vals = layout.T

            row = np.sum(row_vals * powers_of_5)
            col = np.sum(col_vals * powers_of_5)
            # Only calculate for the first octant
            if row - col <= 0 and col <= big_size // 2:
                des_fungi = fast_calc_fung_dist(5, 5, f_type, layout)
                fill_octants(edge, row, col, des_fungi, data)
        
        file_name = f"{i}_dispenser{'s' if i > 1 else ''}_5x5 ({f_name}).csv"
        file_path = os.path.join('disp_optimisation', file_name)
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        print(f"Saved to {file_path} in {1e-9*(time.time_ns() - start_time):.5f} seconds")
        
    print("\nAll simulations completed and exported.")

#####################################
### ADDITIONAL PLOTTING FUNCTIONS ###
#####################################
def n_dim_plot_disps_3d(data, n):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    
    x = np.arange(data.shape[0])
    y = np.arange(data.shape[1])
    X, Y = np.meshgrid(x, y)
    Z = data
    
    surf = ax.plot_surface(X, Y, Z, cmap='viridis')
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    
    # Find all global maxima
    max_value = np.max(data)
    # Find all points that are equal to max_value (within some small epsilon for floating point comparison)
    epsilon = 1e-10
    max_indices = np.where(np.abs(data - max_value) < epsilon)
    
    print(f"Max value: {max_value} at coords:")
    # Plot vertical lines and annotations for all maximum points
    plot_maxs = input("Do you want to plot the maximum points? (y/n): ")
    if plot_maxs.lower() == 'y':
        for x1, y1 in zip(*max_indices):
            z = data[x1, y1]
            # Plot vertical line
            converted_coords = convert_to_base_5_coords(n, x1, y1)
            print(f"\t{converted_coords}")
            ax.plot([x1, x1], [y1, y1], [0, 1.2*z], color='red', linestyle='-', linewidth=3)
            # Annotate point
            ax.text(x1, y1, z, f'({converted_coords})', color='black')
            # Convert and print coordinates
    else:
        for x1, y1 in zip(*max_indices):
            z = data[x1, y1]
            # Plot point
            ax.scatter(x1, y1, 1.2*z, color='red', s=50)
            # Convert and print coordinates

    ax.set_xlabel(f"x-coords for {n} dispensers")
    ax.set_ylabel(f"z-coords for {n} dispensers")
    ax.set_zlabel("Avg Fungi Generated")
    ax.set_title(f"1+2*{n} = {1+2*n}-Dimensional (projected down) plot\n"
                 f"for total desired fungi for {n} dispensers\nMax: {max_value}")
    
    # Customize ticks for base 5 on x and y axes
    x = x[::3 ** (n - 1)]
    y = y[::3 ** (n - 1)]
    ax.set_xticks(x)
    ax.set_yticks(y)
    ax.set_xticklabels([np.base_repr(val, base=5).zfill(n) for val in x], rotation=45)
    ax.set_yticklabels([np.base_repr(val, base=5).zfill(n) for val in y], rotation=45)
    
    plt.show()

def n_dim_plot_disps_2d(data, n, dpi=300, export_only=False):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot the data using imshow
    cax = ax.imshow(data, cmap='viridis', origin='lower')
    
    # Add a colorbar to show the scale
    cbar = fig.colorbar(cax, ax=ax, shrink=0.5, aspect=5)
    cbar.set_label('Avg Fungi Generated')
    
    # Find all global maxima
    max_value = np.max(data)
    epsilon = 1e-10
    max_indices = np.where(np.abs(data - max_value) < epsilon)
    
    if not export_only:
        print(f"Max value: {max_value} at coords:")
    for x1, y1 in zip(*max_indices):
        converted_coords = convert_to_base_5_coords(n, x1, y1)
        if not export_only:
            print(f"\t{converted_coords}")
        # Change the color of the maximum points to red
        data[x1, y1] = np.nan  # Temporarily set to NaN to avoid affecting the color scale
        ax.add_patch(plt.Rectangle((y1 - 0.5, x1 - 0.5), 1, 1, fill=True, color='red'))
    
    # Update the plot with the new data
    cax.set_data(data)
    cax.set_clim(vmin=np.nanmin(data), vmax=np.nanmax(data))  # Adjust color limits to exclude NaN values
    
    lws = LW_BASE_WDTH * np.flip(np.array([0.5 ** i for i in range(n)]))
    for i in range(0, data.shape[0], 5):
        lw = get_line_width(lws, n, i)
        ax.axhline(i - 0.5, color='black', linestyle='-', linewidth=lw)
    for j in range(0, data.shape[1], 5):
        lw = get_line_width(lws, n, j)
        ax.axvline(j - 0.5, color='black', linestyle='-', linewidth=lw)
    
    ax.set_xlabel(f"x-coords for {n} dispensers")
    ax.set_ylabel(f"y-coords for {n} dispensers")
    ax.set_title(f"2D plot for total desired fungi for {n} dispensers\nMax: {max_value}")
    
    # Customize ticks for base 5 on x and y axes
    x = np.arange(data.shape[0])
    y = np.arange(data.shape[1])
    x = x[::2 ** (n - 1)]
    y = y[::2 ** (n - 1)]
    ax.set_xticks(y)
    ax.set_yticks(x)
    ax.set_xticklabels([np.base_repr(val, base=5).zfill(n) for val in y], rotation=45)
    ax.set_yticklabels([np.base_repr(val, base=5).zfill(n) for val in x], rotation=45)
    
    file_name = f"{n} dispenser{'s' if n > 1 else ''} 5x5 dpi={dpi}.png"
    file_path = os.path.join('disp_optimisation', file_name)
    base_name, ext = os.path.splitext(file_path)
    if export_only:
        plt.savefig(file_path, dpi=dpi)
    else:
        plt.show()

def n_dim_plot_disps_3d_plotly(data, n):
    # Create base coordinates
    x = np.arange(data.shape[0])
    y = np.arange(data.shape[1])
    X, Y = np.meshgrid(x, y)
    Z = data

    # Find all global maxima
    max_value = np.max(data)
    epsilon = 1e-10
    max_indices = np.where(np.abs(data - max_value) < epsilon)

    # Create the surface plot
    surface = go.Surface(
        x=X,
        y=Y,
        z=Z,
        colorscale='viridis',
        opacity=1,
        hoverinfo='skip'
    )

    # Create vertical lines for maxima
    lines = []
    for x1, y1 in zip(*max_indices):
        z = data[x1, y1]
        # Create point marker at maximum
        lines.append(
            go.Scatter3d(
                x=[x1],
                y=[y1],
                z=[z],
                mode='markers+text',
                marker=dict(size=5, color='red'),
                text=f'{convert_to_base_5_coords(n, x1, y1)}',
                textfont=dict(size=7),  # Set the font size here
                textposition='top center',
                showlegend=False
            )
        )
    
    fig = go.Figure(data=[surface] + lines)

    # Configure x and y axes in base-5 with automatic tick spacing
    fig.update_layout(
        title=f"1+2*{n} = {1+2*n}-Dimensional (projected down) plot<br>for total desired fungi for {n} dispensers",
        scene=dict(
            xaxis=dict(
                title=f"x-coords for {n} dispensers",
                tickmode='auto',  # Allow Plotly to automatically set tick density
                dtick=2 ** (n - 2),  # Dynamic tick interval based on n
                ticktext=[np.base_repr(i, base=5).zfill(n) for i in x],
                tickvals=x,
                tickangle=-45
            ),
            yaxis=dict(
                title=f"z-coords for {n} dispensers",
                tickmode='auto',  # Automatic tick density adjustment
                dtick=2 ** (n - 2),  # Dynamic tick interval based on n
                ticktext=[np.base_repr(i, base=5).zfill(n) for i in y],
                tickvals=y,
                tickangle=45
            ),
            zaxis=dict(
                title="Avg Fungi Generated",
                range=[0, max(max_value, max_value * n / 2)]
            ),
            aspectratio=dict(x=1, y=1, z=0.3),
            aspectmode='manual',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        width=1300,
        height=800,
        showlegend=False
    )

    # Show the plot
    fig.show()

###############################
### HELPER AND MC FUNCTIONS ###
###############################
def get_line_width(lws, num_disps, axis):
    """Get the line width for the grid based on how many times it's exactly divisible by 5."""
    lw_idx = 0
    for i in range(1, num_disps):
        if axis % (5 ** i) == 0:
            lw_idx += 1
    return lws[lw_idx]

def fill_octants(edge, row, col, des_fungi, data):
    """
    Fill in the other octants of the 5x5 grid based on the first octant.
    """
    data[row, col] = des_fungi                  # Original
    data[row, edge - col] = des_fungi           # Mirror horizontally
    data[col, row] = des_fungi                  # Mirror across the diagonal
    data[col, edge - row] = des_fungi           # Mirror horizontally and across the diagonal

    data[edge - row, col] = des_fungi           # Mirror vertically
    data[edge - row, edge - col] = des_fungi    # Mirror both axes
    data[edge - col, edge - row] = des_fungi    # Mirror both axes and across the diagonal
    data[edge - col, row] = des_fungi           # Mirror vertically and across the diagonal

def to_base_5(num):
    """Convert a number to base 5 and return it as a tuple of its digits."""
    if num == 0:
        return (0,)
    digits = []
    while num > 0:
        digits.append(num % 5)
        num //= 5
    return tuple(reversed(digits))

def convert_to_base_5_coords(n, x, y):
    """Convert two numbers to base 5 coordinates and return as a list of tuples."""
    base_5_x = to_base_5(x)
    base_5_y = to_base_5(y)

    # Pad with zeros on the left
    base_5_x = (0,) * (n - len(base_5_x)) + base_5_x
    base_5_y = (0,) * (n - len(base_5_y)) + base_5_y
    
    # Create a list of tuples from the two base 5 representations
    result = [(base_5_x[i], base_5_y[i]) for i in range(n)]
    
    return result

def fast_calc_fung_dist(length, width, fungus_type, disp_layout):
    if fungus_type == WARPED:
        return warped_calc_fung_dist(length, width, disp_layout)
    
    # 2D array for storing distribution of all the foliage
    foliage_grid = np.zeros((width, length))
    x, y = np.ogrid[:width, :length]

    for (disp_x, disp_y) in disp_layout:
        x1 = np.abs(x - disp_x).astype(int)
        y1 = np.abs(y - disp_y).astype(int)
        
        sel_chance = np.where((x1 > 2) | (y1 > 2), 0,
                            selection_cache[np.minimum(x1, 2), np.minimum(y1, 2)])

        disp_chance = (1 - foliage_grid[disp_x, disp_y])

        foliage_grid += (1 - foliage_grid) * disp_chance * sel_chance

    return np.sum(foliage_grid) / 9

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
    
    # Generate all possible positions (allowing overlap) for n dispensers on the grid
    position_combinations = list(itertools.product(grid_positions, repeat=n))[:5**(2*n)]
    # print(f"position_combinations: {position_combinations} (total: {len(position_combinations)})\n")  # Showing a subset for brevity
    
    result = np.zeros((len(position_combinations), n, 2), dtype=int)
    
    for pos_idx, positions in enumerate(position_combinations):
            result[pos_idx] = positions
    
    return np.array(result)

if __name__ == "__main__":
    command_loop()