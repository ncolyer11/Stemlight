import math
import time
import random
import numpy as np
import pandas as pd

from src.Fast_Dispenser_Distribution import fast_calc_fung_dist, fast_calc_hf_dist
import src.Assets.constants as const
from src.Assets.helpers import resource_path

ACCEPTANCE_RATE = 0.995
REJECTION_POINT = 0.1
UNCLEARED = 0
CLEARED = 1
MAX_ALL_WIDTH = 6
MAX_ALL_LENGTH = 5
MAX_ALL_CYCLES = 5
ALL_RUN_TIME = 100
MAX_ALL_AVG_NUM_DISPS = 10

# Random int function shorthand
rand_s = np.random.randint

class LayoutParamters:
    """A class to store parameters of a playerless core nether tree farm to be optimised"""
    def __init__(self, length, width, fungus_type, disp_layout, num_cycles):
        self.length = length
        self.width = width
        self.fungus_type = fungus_type
        self.disp_layout = disp_layout
        self.num_disps = len(self.disp_layout)
        self.num_cycles = num_cycles
    
    def calculate_temp_bounds(self):
        # Find the lowest energy point
        lowest_energy = self.get_lowest_energy()

        # Create a valid set of coords by passing it through generate_neighbour
        average_solutions = []
        num_disps = self.num_disps
        trials = 300 * num_disps
        # Randomly choose num_disps unique pairs
        for _ in range(trials):
            average_solutions.append(self.generate_random_layout())
        
        # Calculate the average energy of the initial solution
        avg_energy = np.mean([
            fast_calc_fung_dist(
                **average_solutions[i], blocked_blocks=[]
            )[0] for i in range(trials)
        ])

        high_energy_change = avg_energy - lowest_energy
        start_temperature = -high_energy_change / np.log(ACCEPTANCE_RATE)
        end_temperature = -high_energy_change / np.log(REJECTION_POINT)
        return start_temperature, end_temperature, lowest_energy, avg_energy
    
    def generate_random_layout(self):
        length = rand_s(1, MAX_ALL_LENGTH + 1)
        width = rand_s(1, MAX_ALL_WIDTH + 1)
        fungus_type = const.WARPED if np.random.rand() < 0.5 else const.CRIMSON
        is_cleared = rand_s(0,2)

        all_disps = [[x, y, is_cleared] for x in range(width) for y in range(length)]
        coords = np.random.choice(
            len(all_disps),
            min(len(all_disps), rand_s(MAX_ALL_AVG_NUM_DISPS)),
            replace=False
        )
        disp_layout = [all_disps[i] for i in coords]

        num_cycles = rand_s(1, MAX_ALL_CYCLES + 1)

        return {
            'length': length,
            'width': width,
            'fungus_type': fungus_type,
            'disp_layout': disp_layout,
            'num_cycles': num_cycles
        }

    def generate_neighbour(self, current_sol):
        disp_layout = current_sol['disp_layout']
        # Change paramter vals by -1, 0, or 1, ensuring it still remains at a valid value
        length = max(1, min(current_sol['length'] + rand_s(-1, 2), MAX_ALL_LENGTH))
        width = max(1, min(current_sol['width'] + rand_s(-1, 2), MAX_ALL_WIDTH))
        num_cycles = max(1, min(current_sol['num_cycles'] + rand_s(-1, 2), MAX_ALL_CYCLES))
        # Randomly chose between warped or crimson nylium
        fungus_type = const.WARPED if np.random.rand() < 0.5 else const.CRIMSON

        # print("Initial num disps:", len(disp_layout))
        num_disps = max(1, min(len(disp_layout) + rand_s(-1, 2), length * width))
        # print("New num disps:", num_disps)
        # Create a copy of the current solution
        neighbour_disp_layout = disp_layout.copy()
        positions = [[pos[0], pos[1], UNCLEARED] for pos in disp_layout]
        # print("Initial disp layout:", neighbour_disp_layout)
        if num_disps < len(disp_layout):
            # If there's one less dispenser, then randomly remove one from the layout
            neighbour_disp_layout.remove(random.choice(neighbour_disp_layout))
        elif num_disps > len(disp_layout):
            # If there's one more dispenser, then randomly place it at an empty spot on the platform
            new_disp = [rand_s(width), rand_s(length), UNCLEARED]
            while new_disp in positions:
                new_disp = [rand_s(width), rand_s(length), UNCLEARED]
            neighbour_disp_layout.append(new_disp)

        # print("Disp layout after +/- disp:", neighbour_disp_layout)

        # Just straight up remove all excess dispensers
        for i, coords in reversed(list(enumerate(neighbour_disp_layout))):
            if coords[0] >= width or coords[1] >= length:
                del neighbour_disp_layout[i]

        num_disps = len(neighbour_disp_layout)
        # Allow dispenser placements to wander if axis isn't dimensionless
        step_h = 1 if width != 1 else 0
        step_v = 1 if length != 1 else 0

        neighbour_solution = {
            'length': length,
            'width': width,
            'fungus_type': fungus_type,
            'disp_layout': neighbour_disp_layout,
            'num_cycles': num_cycles
        }
        
        # Chose a random number of dispensers to change in a random order
        indexes_to_change = np.random.choice(num_disps, rand_s(max(1, num_disps)), replace=False)
        positions = [[pos[0], pos[1], UNCLEARED] for pos in neighbour_disp_layout]
        for i in indexes_to_change:
            # Randomly select a small change in horizontal and vertical coord (-1, 0, or 1)
            sol_x, sol_y, _ = positions[i]
            # Randomly chose between cleared and non-cleared dispenser if there's at least 1 cleared
            # dispenser in the input field already
            cleared_val = rand_s(0, 2)
            new_coords = [max(0, min(width - 1, sol_x + rand_s(-step_h, step_h + 1))),
                        max(0, min(length - 1, sol_y + rand_s(-step_v, step_v + 1))),
                        cleared_val]

            # Make sure no two coords can be the same
            else_array = positions[:i] + positions[i+1:]
            while any([new_coords[0], new_coords[1]] == coord[:2] for coord in else_array):
                new_coords = [max(0, min(width - 1, new_coords[0] + rand_s(-step_h, step_h + 1))), 
                            max(0, min(length - 1, new_coords[1] + rand_s(-step_v, step_v + 1))),
                            cleared_val]
                # print(new_coords)
                # print(else_array)
                # print(positions)
                # print("loop2", length, width)
        
            # Update the disp_layout with the new coord and its cleared status
            positions[i] = new_coords.copy()
            neighbour_solution['disp_layout'][i] = new_coords

        return neighbour_solution

    # Here 'temperature' is also starting temperature, at least initially
    def simulated_annealing(self, initial_sol, temperature, cooling_rate, min_temperature):
        current_sol = initial_sol
        best_sol = initial_sol
        max_iterations = 1000000
        for i in range(max_iterations):
            if temperature < min_temperature:
                break

            neighbour_sol = self.generate_neighbour(current_sol)
            # print(i)
            # Either desired fungi produced, or potential wart blocks generated
            current_energy = fast_calc_fung_dist(**current_sol, blocked_blocks=[])[0]
            neighbour_energy, bm_for_prod = fast_calc_fung_dist(**neighbour_sol, blocked_blocks=[])

            bm_for_growth = neighbour_energy * const.AVG_BM_TO_GROW_FUNG
            # wart_blocks_prod = fast_calc_hf_dist(**neighbour_sol, blocked_blocks=[])[0]
            wart_blocks_prod = 100
            bm_req = wart_blocks_prod > (bm_for_prod + bm_for_growth) * const.WARTS_PER_BM

            accept_prob = self.acceptance_probability(current_energy, neighbour_energy, temperature)
            if neighbour_energy > current_energy and bm_req or \
                np.random.rand() < accept_prob:
                current_sol = neighbour_sol
                if neighbour_energy > fast_calc_fung_dist(**best_sol, blocked_blocks=[])[0] and bm_req:
                    best_sol = neighbour_sol

            temperature *= cooling_rate

        best_val = fast_calc_fung_dist(**best_sol, blocked_blocks=[])[0]
        return best_sol, best_val

    def run_fast_calc_fung_dist(self, disp_layout=None):
        if disp_layout == None:
            disp_layout = self.disp_layout

        return fast_calc_fung_dist(
            self.length,
            self.width,
            self.fungus_type,
            disp_layout,
            self.num_cycles,
            []
        )

    def run_fast_calc_hf_dist(self, disp_layout=None):
        if disp_layout == None:
            disp_layout = self.disp_layout
        
        return fast_calc_hf_dist(
            self.length,
            self.width,
            self.fungus_type,
            disp_layout,
            self.num_cycles,
            []
        )

    def acceptance_probability(self, current_energy, neighbour_energy, temperature):
        if neighbour_energy > current_energy:
            return 1.0
        else:
            return np.exp((neighbour_energy - current_energy) / temperature)
    
    def get_lowest_energy(self):
        # Return the lowest non-zero layout: a 1-cycle 1x1 crimson platform with a cleared dispenser
        return fast_calc_fung_dist(
            1, 1, const.CRIMSON,
            [[0, 0, CLEARED]],
            1,
            []
        )[0]
    
def optimise_all():
    """Simulated annealing with all paramters as inputs,
    (length, width, nylium type, number placement cleared status and order of dispensers, and
    num cycles) all whilst aiming for at least net positive bone meal return."""
    params = LayoutParamters(
        length=1, 
        width=1, 
        fungus_type=const.WARPED, 
        disp_layout=[[0, 0, UNCLEARED]],
        num_cycles=1
    )

    start_temp, end_temp, *_ = params.calculate_temp_bounds()
    cooling_rate = calculate_cooling_rate(start_temp, end_temp, ALL_RUN_TIME)
    iterations = math.floor(math.log(end_temp / start_temp) / math.log(cooling_rate)) + 1
    print(f"\nStarting temp: {start_temp}",
          f"\nEnding temp: {end_temp}", 
          f"\nCooling rate: {cooling_rate}",
          f"\nIterations: {iterations}")
    
    initial_sol = {
        'length': 1,
        'width': 1,
        'fungus_type': const.WARPED,
        'disp_layout': [[0, 0, UNCLEARED]],
        'num_cycles': 1
    }

    all_optimal_sol, all_optimal_val = params.simulated_annealing(
        initial_sol,
        start_temp,
        cooling_rate,
        end_temp # also known as 'min_temp'
    )

    return all_optimal_sol, all_optimal_val, iterations

def start_optimisation(disp_coords, length, width, wb_per_fungi, fungus_type,
                       run_time, cycles, blocked_coords):
    """Start optimising the function using the simulated annealing algorithm."""
    num_dispensers = len(disp_coords)
    if num_dispensers == 0:
        return [], 0
    cleared_array = [d[2] for d in disp_coords]
    has_cleared = False
    if CLEARED in cleared_array:
        has_cleared = True
    optimise_func = fast_calc_fung_dist
    start_time = time.time()
    # Start with all worst case dispensers off the grid with no clearing
    initial_solution = [[-1, -1, 0] for _ in range(num_dispensers)]
    start_temp, end_temp, *_ = calculate_temp_bounds(num_dispensers, length, width, fungus_type,
                                                     optimise_func, cycles, blocked_coords,
                                                     has_cleared)

    cooling_rate = calculate_cooling_rate(start_temp, end_temp, run_time)
   
    iterations = math.floor(math.log(end_temp / start_temp) / math.log(cooling_rate)) + 1
    print(f"\nStarting temp: {start_temp}",
          f"\nEnding temp: {end_temp}", 
          f"\nCooling rate: {cooling_rate}",
          f"\nIterations: {iterations}")

    optimal_solution, optimal_value = simulated_annealing(
                                        initial_solution, start_temp, cooling_rate, end_temp,
                                        length, width, fungus_type, wb_per_fungi,
                                        optimise_func, cycles, blocked_coords, has_cleared
                                        )
    
    # print("Time taken to optimise:", time.time() - start_time, "seconds")
    # print("Optimal Solution:", optimal_solution)

    return optimal_solution, optimal_value, iterations

def simulated_annealing(initial_sol, temperature, cooling_rate, min_temperature,
                        length, width, fungus_type, wb_per_fungi,
                        optimise_func, cycles, blocked_coords, has_cleared):
    """Simulated annealing algorithm for discrete optimisation of fungus distribution."""
    current_sol = initial_sol
    best_sol = initial_sol
    max_iterations = 100000
    for _ in range(max_iterations):
        if temperature < min_temperature:
            break
        neighbour_sol = generate_neighbour(current_sol, length, width, has_cleared)
        # Either desired fungi produced, or potential wart blocks generated
        current_energy = optimise_func(length, width, fungus_type, current_sol, cycles, blocked_coords)[0]
        neighbour_energy, bm_for_prod = optimise_func(length, width, fungus_type, neighbour_sol, cycles, blocked_coords)

        bm_req = bm_for_prod < wb_per_fungi / const.WARTS_PER_BM - const.AVG_BM_TO_GROW_FUNG
        if neighbour_energy > current_energy and bm_req or \
           np.random.rand() < acceptance_probability(current_energy, neighbour_energy, temperature):
            current_sol = neighbour_sol
            if neighbour_energy > optimise_func(length, width, fungus_type, best_sol, cycles, blocked_coords)[0] \
               and bm_req:
                best_sol = neighbour_sol

        temperature *= cooling_rate
    return best_sol, optimise_func(length, width, fungus_type, best_sol, cycles, blocked_coords)[0]

def acceptance_probability(current_energy, neighbour_energy, temperature):
    """Calculate the probability of accepting a worse solution."""
    if neighbour_energy > current_energy:
        return 1.0
    else:
        return np.exp((neighbour_energy - current_energy) / temperature)

def generate_neighbour(solution, length, width, has_cleared):
    """Generate a new dispenser permutation by altering 1 to all of their coords slightly"""
    step_h = 1 if width != 1 else 0
    step_v = 1 if length != 1 else 0
    rand_s = np.random.randint
    cleared_state = 1
    if has_cleared == True:
        cleared_state = 2

    # Create a copy of the current solution
    neighbour_solution = solution.copy()
    positions = [[pos[0], pos[1], UNCLEARED] for pos in solution]
    # Randomly select coords to change
    indexes_to_change = np.random.choice(len(solution), len(solution), replace=False)
    for i in indexes_to_change:
        # Randomly select a small change in horizontal and vertical coord (-1, 0, or 1)
        sol_x, sol_y, _ = positions[i]
        # Randomly chose between cleared and non-cleared dispenser if there's at least 1 cleared
        # dispenser in the input field already
        cleared_val = rand_s(0, cleared_state)
        new_coords = [max(0, min(width - 1, sol_x + rand_s(-step_h, step_h + 1))),
                      max(0, min(length - 1, sol_y + rand_s(-step_v, step_v + 1))),
                      cleared_val]

        # Make sure no two coords can be the same
        else_array = positions[:i] + positions[i+1:]
        while new_coords in else_array:
            new_coords = [max(0, min(width - 1, new_coords[0] + rand_s(-step_h, step_h + 1))), 
                          max(0, min(length - 1, new_coords[1] + rand_s(-step_v, step_v + 1))),
                          cleared_val]
    
        # Update the solution with the new coord and its cleared status
        positions[i] = new_coords.copy()
        neighbour_solution[i] = new_coords

    return neighbour_solution

def calculate_temp_bounds(N, length, width, fungus_type, optimise_func, cycles, blocked_coords, has_cleared):
    """Calculate the starting temperature for the simulated annealing algorithm."""
    # Find the lowest energy point
    rand_s = np.random.randint
    lowest_energy = get_lowest_energy(N, length, width, fungus_type, optimise_func, cycles, blocked_coords)

    # Create a valid set of coords by passing it through generate_neighbour
    average_solutions = []
    trials = 300*N if optimise_func == fast_calc_fung_dist else 150*N
    for _ in range(trials):
        coords = [[rand_s(0, width), rand_s(0, length), UNCLEARED] for _ in range(N)]
        average_solutions.append(generate_neighbour(coords, length, width, has_cleared))
    
    # Calculate the average energy of the initial solution
    avg_energy = np.mean([
        optimise_func(
            length, width, fungus_type, average_solutions[i], cycles, blocked_coords
        )[0] for i in range(trials)
    ])

    high_energy_change = avg_energy - lowest_energy
    start_temperature = -high_energy_change / np.log(ACCEPTANCE_RATE)
    end_temperature = -high_energy_change / np.log(REJECTION_POINT)
    return start_temperature, end_temperature, lowest_energy, avg_energy

def get_lowest_energy(N, length, width, fungus_type, optimise_func, cycles, blocked_coords):
    # Worst case energy with a single blocked block is every dispenser on a blocked block, 0:
    if len(blocked_coords) > 0:
        return 0
    
    # Otherwise just chuck up all the dispensers in the top left corner
    return optimise_func(
        length, width, fungus_type,
        [[0, 0, UNCLEARED] for _ in range(N)],
        cycles,
        blocked_coords
    )[0]

def calculate_cooling_rate(start_temp, end_temp, run_time):
    # Time taken for the CPU to compute ~one iteration of the simulated annealing algorithm
    # Dependant on hardware, optimise_func, as well as number of permutations
    f = open(resource_path("cpu_benchmark.txt"), "r")
    iter_time = f.readline().strip()
    f.close()
    try:
        # Attempt to convert the iter_time to a float
        cooling_rate = (end_temp / start_temp) ** (float(iter_time) / int(run_time))
    except ValueError:
        # Handle the case where cpu benchmark time is corrupted/unreadable somehow
        with open(resource_path("cpu_benchmark.txt"), "w") as f:
            f.write(str(const.BASE_CPU_ITER_TIME))
        
        # Re-run the calculation using the default BASE_CPU_ITER_TIME as iter_time
        cooling_rate = (end_temp / start_temp) ** (const.BASE_CPU_ITER_TIME / int(run_time))

    return cooling_rate

# Research and development functions #

def output_results(length, width, optimal_func, solution, start_time):
    """Output the results of the optimisation."""
    # print("Time taken:", time.time() - start_time)
    best_coords = np.array(solution)
    # print("Optimal coords: \n", best_coords)
    # print("Optimal value: ", optimal_func(solution))
    # Print the location of max_rates_coords in a grid on terminal
    for row in range(length):
        for col in range(width):
            if [row, col] in solution:
                print(f'[{solution.index([row, col])}]', end='')
            else:
                print('[ ]', end='')
        # print()
    # print()
    
def run_optimisation(length, width):
    """Run the optimisation for 1 to 10 dispensers and write the results to an Excel file."""
    results = pd.DataFrame(columns=["Num_Dispensers", "Lowest_Energy",
                                    "Average_Energy", "Start_Temperature"])

    for num_dispensers in range(1, 11):
        start_temperature, end_temperature, lowest_energy, avg_energy = \
            calculate_temp_bounds(num_dispensers, length, width)
        results = pd.concat([results, pd.DataFrame([{
            "Num_Dispensers": num_dispensers, 
            "Lowest_Energy": lowest_energy, 
            "Average_Energy": avg_energy, 
            "Start_Temperature": start_temperature,
            "End_Temperature": end_temperature}], index=[0])], ignore_index=True)

    results.to_excel("optimisation_results.xlsx", index=False)

def plot_cooling_rate_data():
    """Analyse how different cooling rates affect accuracy using plotted emperical data."""
    num_dispensers = [5,6]
    cooling_rates = [0.9995, 0.9999]

    # Create a DataFrame to store the results
    df = pd.DataFrame(columns=["Num_Dispensers", "Cooling_Rate", "Mean_Value", 
                               "Actual_Value", "Accuracy"])

    for disp in num_dispensers:
        for rate in cooling_rates:
            # print("\nDispenser", disp, "'s cooling rate:", rate)
            results = []
            for _ in range((100*disp)//3):
                result, *_ = start_optimisation(disp, rate)
                results.append(result)
            mean_value = np.mean(results)
            mogged_rate = 0.999995 if disp >= 5 else 0.9995
            actual_value, *_ = start_optimisation(disp, mogged_rate)
            # print("Mean value:", mean_value)
            # print("Actual value:", actual_value)
            # print("Accuracy:", mean_value / actual_value)

            # Add the results to the DataFrame
            df = pd.concat([df, pd.DataFrame([{
                "Num_Dispensers": disp, 
                "Cooling_Rate": rate, 
                "Mean_Value": mean_value, 
                "Actual_Value": actual_value, 
                "Accuracy": mean_value / actual_value}], index=[0])], ignore_index=True)

    # Write the DataFrame to an Excel file
    df.to_excel("cooling_rate_data.xlsx", index=False)

if __name__ == "__main__":
    for i in range(1, 11):
        start_optimisation(i, 5)
