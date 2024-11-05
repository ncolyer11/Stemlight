import math
import time
import pandas as pd
import numpy as np
from numpy.random import randint as rand_s

from src.Fast_Dispenser_Distribution import fast_calc_fung_dist
from src.Assets.constants import *
from src.Assets.helpers import resource_path
from src.Assets.data_classes import *

ACCEPTANCE_RATE = 0.995
REJECTION_POINT = 0.1
MAX_ITERATIONS = 1000000
NULL_TIME = 0

def start_optimisation(L: PlayerlessCore) -> Tuple[List[Dispenser], float, int]:
    """Start optimising the function using the simulated annealing algorithm."""
    if L.num_disps == 0:
        return [], 0
    has_cleared = False
    if CLEARED in [d.cleared for d in L.disp_coords]:
        has_cleared = True
    optimise_func = fast_calc_fung_dist
    temps = calculate_temp_bounds(L, optimise_func, has_cleared)
    # Start with all worst case dispensers off the grid with no clearing
    init_sol = [Dispenser(-1, -1, NULL_TIME, UNCLEARED) for _ in range(L.num_disps)]
    S = SimAnnealingParams(
        optimise_func=optimise_func,
        optimal_value=0,
        initial_solution=init_sol,
        current_solution=None,
        best_solution=None,
        start_temp=temps[0],               
        end_temp=temps[1],  
        cooling_rate=calculate_cooling_rate(temps[0], temps[1], L.run_time),
        max_iterations=MAX_ITERATIONS
    )
    S.current_solution = S.initial_solution # Start with the worst case solution
    S.best_solution = S.initial_solution
    optimise_func = fast_calc_fung_dist
    start_time = time.time()
   
    iterations = math.floor(math.log(S.end_temp / S.start_temp) / math.log(S.cooling_rate)) + 1
    print(f"\nStarting temp: {S.start_temp}",
          f"\nEnding temp: {S.end_temp}", 
          f"\nCooling rate: {S.cooling_rate}",
          f"\nIterations: {iterations}")

    out = simulated_annealing(L, S, has_cleared)
    
    print("Time taken to optimise:", time.time() - start_time, "seconds")

    return out.best_solution, out.optimal_value, iterations

def simulated_annealing(
    L: PlayerlessCore,
    S: SimAnnealingParams,
    has_cleared=False
) -> SimAnnealingParams:
    """Simulated annealing algorithm for discrete optimisation of fungus distribution."""
    temperature = S.start_temp
    print("wart blocks eff:", L.warts_effic)
    S.optimal_value = 0
    for _ in range(S.max_iterations):
        if temperature < S.end_temp:
            break
        # NOTE GENERATE NEIGHBOUR IS NOT CAUSING THE ISSUE HERE
        neighbour_sol = generate_neighbour(S.current_solution, L.size, has_cleared)
        # Either desired fungi produced, or potential wart blocks generated
        current_energy = S.optimise_func(L.size.length, L.size.width, L.nylium_type,
                                         S.current_solution, L.cycles, L.blocked_blocks)[0]
        neighbour_energy, bm_for_prod = S.optimise_func(L.size.length, L.size.width, L.nylium_type,
                                                        neighbour_sol, L.cycles, L.blocked_blocks)
        bm_req = bm_for_prod < L.warts_effic / WARTS_PER_BM - AVG_BM_TO_GROW_FUNG
        if neighbour_energy > current_energy and bm_req or \
           np.random.rand() < acceptance_probability(current_energy, neighbour_energy, temperature):
            S.current_solution = neighbour_sol
            if bm_req and neighbour_energy > S.optimal_value:
                S.best_solution = neighbour_sol
                S.optimal_value = S.optimise_func(L.size.length, L.size.width, L.nylium_type,
                                                  S.best_solution, L.cycles, L.blocked_blocks)[0]

        temperature *= S.cooling_rate
    S.optimal_value
    print("Optimal value:", S.optimal_value)
    print(S.best_solution)
    return S

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
    cleared_state = 1
    if has_cleared == True:
        cleared_state = 2

    # Create a copy of the current solution
    neighbour_solution = solution.copy()
    # Randomly select coords to change
    indexes_to_change = np.random.choice(len(solution), len(solution), replace=False)
    positions = [[pos.row, pos.col, NULL_TIME, UNCLEARED] for pos in neighbour_solution]
    for i in indexes_to_change:
        # Randomly select a small change in horizontal and vertical coord (-1, 0, or 1)
        sol_row, sol_col, *_ = positions[i]
        # Randomly chose between cleared and non-cleared dispenser if there's at least 1 cleared
        # dispenser in the input field already
        cleared_val = rand_s(0, cleared_state)
        new_coords = [
            max(0, min(size.width - 1, sol_row + rand_s(-step_h, step_h + 1))),
            max(0, min(size.length - 1, sol_col + rand_s(-step_v, step_v + 1))),
            NULL_TIME, cleared_val
        ]

        # Make sure no two coords can be the same
        else_array = positions[:i] + positions[i+1:]
        while any([new_coords[0], new_coords[1]] == coord[:2] for coord in else_array):
            new_coords = [
                max(0, min(size.width - 1, new_coords[0] + rand_s(-step_h, step_h + 1))), 
                max(0, min(size.length - 1, new_coords[1] + rand_s(-step_v, step_v + 1))),
                NULL_TIME, cleared_val
            ]
    
        # Update the solution with the new coord and its cleared status
        positions[i] = new_coords.copy()
        neighbour_solution[i] = new_coords
    neighbour_solution = [Dispenser(*coords) for coords in neighbour_solution]
    return neighbour_solution

def calculate_temp_bounds(
    L: PlayerlessCore,
    optimise_func: Callable,
    has_cleared: ClearedStatus
) -> Tuple[float, float, float, float]:
    """Calculate the starting temperature for the simulated annealing algorithm."""
    # Find the lowest energy point
    rand_s = np.random.randint
    lowest_energy = get_lowest_energy(L, optimise_func)

    # Create a valid set of coords by passing it through generate_neighbour
    average_solutions = []
    trials = 300 * L.num_disps if optimise_func == fast_calc_fung_dist else 150 * L.num_disps
    for _ in range(trials):
        coords = [
            Dispenser(
                rand_s(0, L.size.width), rand_s(0, L.size.length), NULL_TIME, UNCLEARED
            ) for _ in range(L.num_disps)
        ]
        average_solutions.append(
            generate_neighbour(coords, L.size, has_cleared)
        )
    
    # Calculate the average energy of the initial solution
    avg_energy = np.mean([
        optimise_func(
            L.size.length, L.size.width, L.nylium_type, average_solutions[i], L.cycles, 
            L.blocked_blocks
        )[0] for i in range(trials)
    ])

    high_energy_change = avg_energy - lowest_energy
    start_temperature = -high_energy_change / np.log(ACCEPTANCE_RATE)
    end_temperature = -high_energy_change / np.log(REJECTION_POINT)
    return start_temperature, end_temperature, lowest_energy, avg_energy

def get_lowest_energy(L: PlayerlessCore, optimise_func: Callable) -> float:
    """
    Get the lowest energy point of the optimisation space. I.e. the worst dispenser layout possible.
    """
    # Worst case energy with a single blocked block is every dispenser on a blocked block, 0:
    if len(L.blocked_blocks) > 0:
        return 0
    # Otherwise just chuck up all the dispensers in the top left corner
    return optimise_func(
        L.size.length, L.size.width, L.nylium_type,
        [Dispenser(0, 0, NULL_TIME, UNCLEARED) for _ in range(L.num_disps)],
        L.cycles,
        L.blocked_blocks
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
