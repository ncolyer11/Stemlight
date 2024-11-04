import math
import time
import random
import numpy as np
import pandas as pd
from numpy.random import randint as rand_s

from src.Fast_Dispenser_Distribution import fast_calc_fung_dist, fast_calc_hf_dist
from src.Assets.constants import *
from src.Assets.helpers import resource_path
from src.Assets.data_classes import *

ACCEPTANCE_RATE = 0.995
REJECTION_POINT = 0.1
MAX_ALL_WIDTH = 5
MAX_ALL_LENGTH = 4
MAX_ALL_CYCLES = 5
ALL_RUN_TIME = 10
MAX_ALL_AVG_NUM_DISPS = 10
MAX_ITER = 1000000

class LayoutParamters:
    """A class to store parameters of a playerless core nether tree farm to be optimised"""
    def __init__(self, length, width, nylium_type, disp_coords, cycles):
        self.length = length
        self.width = width
        self.nylium_type = nylium_type
        self.disp_coords = disp_coords
        self.num_disps = len(self.disp_coords)
        self.cycles = cycles
    
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
        nylium_type = WARPED if np.random.rand() < 0.5 else CRIMSON
        is_cleared = rand_s(0,2)

        all_disps = [[x, y, is_cleared] for x in range(width) for y in range(length)]
        coords = np.random.choice(
            len(all_disps),
            min(len(all_disps), rand_s(MAX_ALL_AVG_NUM_DISPS)),
            replace=False
        )
        disp_coords = [all_disps[i] for i in coords]

        cycles = rand_s(1, MAX_ALL_CYCLES + 1)

        return {
            'length': length,
            'width': width,
            'nylium_type': nylium_type,
            'disp_coords': disp_coords,
            'cycles': cycles
        }

    def generate_neighbour(self, current_sol):
        disp_coords = current_sol['disp_coords']
        # Change paramter vals by -1, 0, or 1, ensuring it still remains at a valid value
        length = max(1, min(current_sol['length'] + rand_s(-1, 2), MAX_ALL_LENGTH))
        width = max(1, min(current_sol['width'] + rand_s(-1, 2), MAX_ALL_WIDTH))
        cycles = max(1, min(current_sol['cycles'] + rand_s(-1, 2), MAX_ALL_CYCLES))
        # Randomly chose between warped or crimson nylium
        nylium_type = WARPED if np.random.rand() < 0.5 else CRIMSON

        # print("Initial num disps:", len(disp_coords))
        num_disps = max(1, min(len(disp_coords) + rand_s(-1, 2), length * width))
        # print("New num disps:", num_disps)
        # Create a copy of the current solution
        neighbour_disp_coords = disp_coords.copy()
        positions = [[pos[0], pos[1], UNCLEARED] for pos in disp_coords]
        # print("Initial disp layout:", neighbour_disp_coords)
        if num_disps < len(disp_coords):
            # If there's one less dispenser, then randomly remove one from the layout
            neighbour_disp_coords.remove(random.choice(neighbour_disp_coords))
        elif num_disps > len(disp_coords):
            # If there's one more dispenser, then randomly place it at an empty spot on the platform
            new_disp = [rand_s(width), rand_s(length), UNCLEARED]
            while new_disp in positions:
                new_disp = [rand_s(width), rand_s(length), UNCLEARED]
            neighbour_disp_coords.append(new_disp)

        # print("Disp layout after +/- disp:", neighbour_disp_coords)

        # Just straight up remove all excess dispensers
        for i, coords in reversed(list(enumerate(neighbour_disp_coords))):
            if coords[0] >= width or coords[1] >= length:
                del neighbour_disp_coords[i]

        num_disps = len(neighbour_disp_coords)
        # Allow dispenser placements to wander if axis isn't dimensionless
        step_h = 1 if width != 1 else 0
        step_v = 1 if length != 1 else 0

        neighbour_solution = {
            'length': length,
            'width': width,
            'nylium_type': nylium_type,
            'disp_coords': neighbour_disp_coords,
            'cycles': cycles
        }
        
        # Chose a random number of dispensers to change in a random order
        indexes_to_change = np.random.choice(num_disps, rand_s(max(1, num_disps)), replace=False)
        positions = [[pos[0], pos[1], UNCLEARED] for pos in neighbour_disp_coords]
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
        
            # Update the disp_coords with the new coord and its cleared status
            positions[i] = new_coords.copy()
            neighbour_solution['disp_coords'][i] = new_coords

        return neighbour_solution

    # Here 'temperature' is also starting temperature, at least initially
    def simulated_annealing(self, initial_sol, temperature, cooling_rate, min_temperature):
        current_sol = initial_sol
        best_sol = initial_sol
        max_iterations = 1000000
        for i in range(max_iterations):
            if (i % 1000 == 0):
                print(i)
            if temperature < min_temperature:
                break

            neighbour_sol = self.generate_neighbour(current_sol)
            # Either desired fungi produced, or potential wart blocks generated
            current_energy = fast_calc_fung_dist(**current_sol, blocked_blocks=[])[0]
            neighbour_energy, bm_for_prod = fast_calc_fung_dist(**neighbour_sol, blocked_blocks=[])

            bm_for_growth = neighbour_energy * AVG_BM_TO_GROW_FUNG
            wart_blocks_prod = 100
            bm_req = wart_blocks_prod > (bm_for_prod + bm_for_growth) * WARTS_PER_BM

            accept_prob = self.acceptance_probability(current_energy, neighbour_energy, temperature)
            if neighbour_energy > current_energy and bm_req or \
                np.random.rand() < accept_prob:
                current_sol = neighbour_sol
                if neighbour_energy > fast_calc_fung_dist(**best_sol, blocked_blocks=[])[0] and bm_req:
                    best_sol = neighbour_sol

            temperature *= cooling_rate

        best_val = fast_calc_fung_dist(**best_sol, blocked_blocks=[])[0]
        return best_sol, best_val

    def run_fast_calc_fung_dist(self, disp_coords=None):
        if disp_coords == None:
            disp_coords = self.disp_coords

        return fast_calc_fung_dist(
            self.length,
            self.width,
            self.nylium_type,
            disp_coords,
            self.cycles,
            []
        )

    def run_fast_calc_hf_dist(self, disp_coords=None):
        if disp_coords == None:
            disp_coords = self.disp_coords
        
        return fast_calc_hf_dist(
            self.length,
            self.width,
            self.nylium_type,
            disp_coords,
            self.cycles,
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
            1, 1, CRIMSON,
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
        nylium_type=WARPED, 
        disp_coords=[[0, 0, UNCLEARED]],
        cycles=1
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
        'nylium_type': WARPED,
        'disp_coords': [[0, 0, UNCLEARED]],
        'cycles': 1
    }

    all_optimal_sol, all_optimal_val = params.simulated_annealing(
        initial_sol,
        start_temp,
        cooling_rate,
        end_temp # also known as 'min_temp'
    )

    return all_optimal_sol, all_optimal_val, iterations

def start_optimisation(L: PlayerlessCore) -> Tuple[List[Dispenser], float, int]:
    """Start optimising the function using the simulated annealing algorithm."""
    num_dispensers = len(L.disp_coords)
    if num_dispensers == 0:
        return [], 0
    cleared_array = [d[2] for d in L.disp_coords]
    has_cleared = False
    if CLEARED in cleared_array:
        has_cleared = True
    optimise_func = fast_calc_fung_dist
    temps = calculate_temp_bounds(L, num_dispensers, optimise_func, has_cleared)
    S = SimAnnealingParams(
        optimise_func=optimise_func,
        initial_solution=[[-1, -1, 0] for _ in range(num_dispensers)], # Start with all worst case
        start_temp=temps[0],                                           # dispensers off the grid
        end_temp=temps[1],                                             # with no clearing
        cooling_rate=calculate_cooling_rate(temps[0], temps[1], L.run_time),
        max_iter=MAX_ITER
    )
    optimise_func = fast_calc_fung_dist
    start_time = time.time()
   
    iterations = math.floor(math.log(S.end_temp / S.start_temp) / math.log(S.cooling_rate)) + 1
    print(f"\nStarting temp: {S.start_temp}",
          f"\nEnding temp: {S.end_temp}", 
          f"\nCooling rate: {S.cooling_rate}",
          f"\nIterations: {iterations}")

    optimal_solution, optimal_value = simulated_annealing(L, S, has_cleared)
    
    print("Time taken to optimise:", time.time() - start_time, "seconds")
    # print("Optimal Solution:", optimal_solution)

    return optimal_solution, optimal_value, iterations

def simulated_annealing(
    L: PlayerlessCore,
    S: SimAnnealingParams,
    has_cleared=False
) -> Tuple[List[Dispenser], float]:
    """Simulated annealing algorithm for discrete optimisation of fungus distribution."""
    current_sol = S.initial_sol
    best_sol = S.initial_sol
    for _ in range(S.max_iterations):
        if temperature < S.min_temperature:
            break
        neighbour_sol = generate_neighbour(current_sol, L.size, has_cleared)
        # Either desired fungi produced, or potential wart blocks generated
        current_energy = S.optimise_func(L.size.length, L.size.width, L.nylium_type, current_sol, L.cycles, 
                                         L.blocked_coords)[0]
        neighbour_energy, bm_for_prod = S.optimise_func(L.size.length, L.size.width, L.nylium_type, neighbour_sol,
                                                        L.cycles, L.blocked_coords)

        bm_req = bm_for_prod < L.warts_effic / WARTS_PER_BM - AVG_BM_TO_GROW_FUNG
        if neighbour_energy > current_energy and bm_req or \
           np.random.rand() < acceptance_probability(current_energy, neighbour_energy, temperature):
            current_sol = neighbour_sol
            if neighbour_energy > S.optimise_func(L.size.length, L.size.width, L.nylium_type, best_sol, L.cycles,
                                                  L.blocked_coords)[0] and bm_req:
                best_sol = neighbour_sol

        temperature *= S.cooling_rate
    return best_sol, S.optimise_func(L.size.length, L.size.width, L.nylium_type, best_sol, L.cycles, L.blocked_coords)[0]

def acceptance_probability(current_energy, neighbour_energy, temperature):
    """Calculate the probability of accepting a worse solution."""
    if neighbour_energy > current_energy:
        return 1.0
    else:
        return np.exp((neighbour_energy - current_energy) / temperature)

def generate_neighbour(solution: Any, size: Dimensions, has_cleared: ClearedStatus):
    """Generate a new dispenser permutation by altering 1 to all of their coords slightly"""
    step_h = 1 if size.width != 1 else 0
    step_v = 1 if size.length != 1 else 0
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
        new_coords = [max(0, min(size.width - 1, sol_x + rand_s(-step_h, step_h + 1))),
                      max(0, min(size.length - 1, sol_y + rand_s(-step_v, step_v + 1))),
                      cleared_val]

        # Make sure no two coords can be the same
        else_array = positions[:i] + positions[i+1:]
        while new_coords in else_array:
            new_coords = [max(0, min(size.width - 1, new_coords[0] + rand_s(-step_h, step_h + 1))), 
                          max(0, min(size.length - 1, new_coords[1] + rand_s(-step_v, step_v + 1))),
                          cleared_val]
    
        # Update the solution with the new coord and its cleared status
        positions[i] = new_coords.copy()
        neighbour_solution[i] = new_coords

    return neighbour_solution

def calculate_temp_bounds(L: PlayerlessCore, optimise_func: Callable, has_cleared: ClearedStatus):
    """Calculate the starting temperature for the simulated annealing algorithm."""
    # Find the lowest energy point
    rand_s = np.random.randint
    lowest_energy = get_lowest_energy(L)

    # Create a valid set of coords by passing it through generate_neighbour
    average_solutions = []
    trials = 300 * L.num_disps if optimise_func == fast_calc_fung_dist else 150 * L.num_disps
    for _ in range(trials):
        coords = [[
            rand_s(0, L.size.width), rand_s(0, L.size.length), UNCLEARED
            ] for _ in range(L.num_disps)
        ]
        average_solutions.append(
            generate_neighbour(coords, L.size.length, L.size.width,has_cleared)
        )
    
    # Calculate the average energy of the initial solution
    avg_energy = np.mean([
        optimise_func(
            L.size.length, L.size.width, L.nylium_type, average_solutions[i], L.cycles, 
            L.blocked_coords
        )[0] for i in range(trials)
    ])

    high_energy_change = avg_energy - lowest_energy
    start_temperature = -high_energy_change / np.log(ACCEPTANCE_RATE)
    end_temperature = -high_energy_change / np.log(REJECTION_POINT)
    return start_temperature, end_temperature, lowest_energy, avg_energy

def get_lowest_energy(L: PlayerlessCore, optimise_func: Callable):
    # Worst case energy with a single blocked block is every dispenser on a blocked block, 0:
    if len(L.blocked_coords) > 0:
        return 0
    
    # Otherwise just chuck up all the dispensers in the top left corner
    return optimise_func(
        L.size.length, L.size.width, L.nylium_type,
        [[0, 0, UNCLEARED] for _ in range(L.num_disps)],
        L.cycles,
        L.blocked_coords
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
            f.write(str(BASE_CPU_ITER_TIME))
        
        # Re-run the calculation using the default BASE_CPU_ITER_TIME as iter_time
        cooling_rate = (end_temp / start_temp) ** (BASE_CPU_ITER_TIME / int(run_time))

    return cooling_rate

######################################
# Research and development functions #
######################################
def output_results(length, width, optimal_func, solution, start_time):
    """Output the results of the optimisation."""
    # print("Time taken:", time.time() - start_time)
    best_coords = np.array(solution)
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
