import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from random import randint
from random import random as rand
from time import time
from src.Assets.constants import *

# Define key points and weights
A, B, C, D, E, F = (2, 2), (1, 2), (0, 2), (1, 1), (0, 1), (0, 0)
keys = [A, B, C, D, E, F]
weights = np.array([4, 8, 4, 4, 4, 1])  # weights for A, B, C, D, E, F
categories = ["foliage" , "fungus"]#"sprouts", "twisting"

# Initialize totals as arrays
totals = {category: np.zeros(len(keys)) for category in categories}
weighted_totals = {category: [] for category in categories}  # Store weighted totals over time

# Number of cycles
CYCLES_P_SEC = 15783 # ~15783 cycles can be computed per second on my pc
num_cycles = int(CYCLES_P_SEC * 3600 * 9.5) 

# Initialize data storage for plotting
cycle_steps = num_cycles // 100  # 20 evenly spaced intervals
plot_data = {category: {key: [] for key in keys} for category in categories}
cycle_list = []

# Start the simulation
start_time = time()
for c in range(1, num_cycles + 1):
    curr_total = {category: np.zeros(len(keys)) for category in categories}
    
    # Simulate foliage and fungus placement
    for _ in range(FUNG_SPREAD_RAD ** 2):
        (x, y) = (randint(0, 2) - randint(0, 2), randint(0, 2) - randint(0, 2))
        if (x, y) in keys:
            # Try to generate warped fungi
            if rand() < CRMS_FUNG_CHANCE and curr_total["foliage"][keys.index((x, y))] == 0:
                curr_total["fungus"][keys.index((x, y))] = 1
            curr_total["foliage"][keys.index((x, y))] = 1

    # # Sprouts placement
    # for _ in range(FUNG_SPREAD_RAD ** 2):
    #     (x, y) = (randint(0, 2) - randint(0, 2), randint(0, 2) - randint(0, 2))
    #     if (x, y) in keys:
    #         idx = keys.index((x, y))
    #         if curr_total["foliage"][idx] == 0:
    #             curr_total["sprouts"][idx] = 1
    
    # Twisting placement
    # # Hi! btw you'll need like 3x more offsets for the 3x3 grid of twisting vines :D
    # if curr_total["foliage"][keys.index(F)] == 0 and \
    #    curr_total["sprouts"][keys.index(F)] == 0 and randint(0, 7) == 0:
    #     for _ in range(FUNG_SPREAD_RAD ** 2):
    #         (x, y), z = (randint(-3, 3), randint(-3, 3)), randint(-1, 1)
    #         if z in [0, 1] and (x, y) in keys:
    #             idx = keys.index((x, y))
    #             if curr_total["foliage"][idx] == 0 and curr_total["sprouts"][idx] == 0:
    #                 curr_total["twisting"][idx] = 1
    
    # Update totals
    for category in categories:
        totals[category] += curr_total[category]

    # Collect data for plotting every 1/20th of cycles
    if c % cycle_steps == 0:
        elapsed_time = time() - start_time
        est_time_remaining = elapsed_time / c * (num_cycles - c)
        print(f"Cycle {c} ({c / num_cycles * 100:.0f}%) completed in {elapsed_time:.3f}s (est time remaining: {est_time_remaining:.3f}s)\n")
        cycle_list.append(c)
        for category in categories:
            # Collect individual key data
            for idx, key in enumerate(keys):
                plot_data[category][key].append(totals[category][idx] / c)
            
            # Calculate weighted total and store it
            weighted_total = np.dot(weights, totals[category]) / c
            weighted_totals[category].append(weighted_total)

print(f"Foliage distribution simulated in {time() - start_time} seconds")

# Plotting
fig, ax = plt.subplots(len(categories) + 1, 1, figsize=(10, 10), sharex=True)
fig.suptitle("Cumulative Values Over Time for Each Coordinate and Weighted Total")

# Plot individual coordinates with min y-axis value set to 0
for i, category in enumerate(categories):
    for key in keys:
        ax[i].plot(cycle_list, plot_data[category][key], label=f"{key}")
    ax[i].set_ylabel(f"{category} Total")
    ax[i].legend(loc="upper left", fontsize="small")
    ax[i].set_ylim(bottom=0)  # Set minimum y-axis value to 0

# Plot weighted totals with logarithmic scale
for category in categories:
    ax[-1].plot(cycle_list, weighted_totals[category], label=f"{category} Weighted Total")
ax[-1].set_ylabel("Weighted Total Crimson")
ax[-1].set_xlabel("Cycle")
ax[-1].legend(loc="upper left", fontsize="small")
ax[-1].set_yscale("log")  # Apply log scale to the weighted totals plot
# ax[-1].set_ylim(bottom=1)  # Set a lower bound of 1 for the log scale to avoid issues with zero values

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Preparing data for Excel with formatted headers
header = []
for category in categories:
    header.extend([f"{category}_{key}" for key in keys])
header.extend([f"weighted_{category}" for category in categories])
header.append("cycle")

# Organize data in columns and calculate final row with 18000 multiplier
data = {f"{category}_{key}": plot_data[category][key] for category in categories for key in keys}
data.update({f"weighted_{category}": weighted_totals[category] for category in categories})
data["cycle"] = cycle_list

# Final row with 18,000 multiplier
final_row = []
for category in categories:
    final_row.extend([18000 * plot_data[category][key][-1] for key in keys])
final_row.extend([18000 * weighted_totals[category][-1] for category in categories])
final_row.append("Final/h")

# Convert data to DataFrame and add final row
df = pd.DataFrame(data, columns=header)
df.loc[len(df)] = final_row

# Save to Excel with formatting
output_path = "crimson_simulation_results.xlsx"
df.to_excel(output_path, index=False)

print(f"Simulation complete. Data saved to '{output_path}'.")

plt.show()

# NOTE getting 24.5 twisting vines/h for corner thing A