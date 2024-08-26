import math
import time
import numpy as np
import pandas as pd

from src.Fast_Dispenser_Distribution import fast_calc_fung_dist, fast_calc_hf_dist
import src.Assets.constants as const

ACCEPTANCE_RATE = 0.995
REJECTION_POINT = 0.1
UNCLEARED = 0
CLEARED = 1

def start_optimisation(disp_coords, length, width, wb_per_fungi, f_type,
                       run_time, cycles, blocked_coords):
    """Start optimising the function using the simulated annealing algorithm."""
    cleared_array = [d[2] for d in disp_coords]
    has_cleared = False
    if CLEARED in cleared_array:
        has_cleared = True
    optimise_func = fast_calc_fung_dist
    num_dispensers = len(disp_coords)
    if num_dispensers == 0:
        return [], 0
    start_time = time.time()
    # Start with all worst case dispensers off the grid with no clearing
    initial_solution = [[-1, -1, 0] for _ in range(num_dispensers)]
    start_temp, end_temp, *_ = calculate_temp_bounds(num_dispensers, length, width, f_type,
                                                     optimise_func, cycles, blocked_coords,
                                                     cleared_array)
    # Time taken for the CPU to compute ~one iteration of the simulated annealing algorithm
    # Dependant on hardware, optimise_func, as well as number of permutations
    f = open("cpu_benchmark.txt", "r")
    iter_time = f.readline().strip()
    f.close()
    try:
        # Attempt to convert the iter_time to a float
        cooling_rate = (end_temp / start_temp) ** (float(iter_time) / int(run_time))
    except ValueError:
        # Handle the case where cpu benchmark time is corrupted/unreadable somehow
        with open("cpu_benchmark.txt", "w") as f:
            f.write(str(const.BASE_CPU_ITER_TIME))
        
        # Re-run the calculation using the default BASE_CPU_ITER_TIME as iter_time
        cooling_rate = (end_temp / start_temp) ** (const.BASE_CPU_ITER_TIME / int(run_time))
    
    iterations = math.floor(math.log(end_temp / start_temp) / math.log(cooling_rate)) + 1
    print(f"\nStarting temp: {start_temp}",
          f"\nEnding temp: {end_temp}", 
          f"\nCooling rate: {cooling_rate}",
          f"\nIterations: {iterations}")

    optimal_solution, optimal_value = simulated_annealing(
                                        initial_solution, start_temp, cooling_rate, end_temp,
                                        length, width, f_type, wb_per_fungi,
                                        optimise_func, cycles, blocked_coords, has_cleared
                                        )
    
    print("Time taken to optimise:", time.time() - start_time, "seconds")
    print("Optimal Solution:", optimal_solution)

    return optimal_solution, optimal_value, iterations

def simulated_annealing(initial_sol, temperature, cooling_rate, min_temperature,
                        length, width, f_type, wb_per_fungi,
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
        current_energy = optimise_func(length, width, f_type, current_sol, cycles, blocked_coords)[0]
        neighbour_energy, bm_for_prod = optimise_func(length, width, f_type, neighbour_sol, cycles, blocked_coords)
        # print("n sol: ", neighbour_sol)

        bm_req = bm_for_prod < wb_per_fungi / const.WARTS_PER_BM - const.AVG_BM_TO_GROW_FUNG
        if neighbour_energy > current_energy and bm_req or \
           np.random.rand() < acceptance_probability(current_energy, neighbour_energy, temperature):
            current_sol = neighbour_sol
            if neighbour_energy > optimise_func(length, width, f_type, best_sol, cycles, blocked_coords)[0] \
               and bm_req:
                best_sol = neighbour_sol

        temperature *= cooling_rate
    # print("best sol: ", best_sol)
    return best_sol, optimise_func(length, width, f_type, best_sol, cycles, blocked_coords)[0]

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

def calculate_temp_bounds(N, length, width, f_type, optimise_func, cycles, blocked_coords, has_cleared):
    """Calculate the starting temperature for the simulated annealing algorithm."""
    # Find the lowest energy point
    rand_s = np.random.randint
    lowest_energy = get_lowest_energy(N, length, width, f_type, optimise_func, cycles, blocked_coords)

    # Create a valid set of coords by passing it through generate_neighbour
    average_solutions = []
    trials = 300*N if optimise_func == fast_calc_fung_dist else 150*N
    for _ in range(trials):
        coords = [[rand_s(0, width), rand_s(0, length), UNCLEARED] for _ in range(N)]
        average_solutions.append(generate_neighbour(coords, length, width, has_cleared))
    
    # Calculate the average energy of the initial solution
    avg_energy = np.mean([
        optimise_func(
            length, width, f_type, average_solutions[i], cycles, blocked_coords
        )[0] for i in range(trials)
    ])

    high_energy_change = avg_energy - lowest_energy
    start_temperature = -high_energy_change / np.log(ACCEPTANCE_RATE)
    end_temperature = -high_energy_change / np.log(REJECTION_POINT)
    return start_temperature, end_temperature, lowest_energy, avg_energy

def get_lowest_energy(N, length, width, f_type, optimise_func, cycles, blocked_coords):
    # Worst case energy with a single blocked block is every dispenser on a blocked block, 0:
    if len(blocked_coords) > 0:
        return 0
    
    # Otherwise just chuck up all the dispensers in the top left corner
    return optimise_func(
        length, width, f_type,
        [[0, 0, UNCLEARED] for _ in range(N)],
        cycles,
        blocked_coords
    )[0]

def output_results(length, width, optimal_func, solution, start_time):
    """Output the results of the optimisation."""
    print("Time taken:", time.time() - start_time)
    best_coords = np.array(solution)
    print("Optimal coords: \n", best_coords)
    print("Optimal value: ", optimal_func(solution))
        # Print the location of max_rates_coords in a grid on terminal
    for row in range(length):
        for col in range(width):
            if [row, col] in solution:
                print(f'[{solution.index([row, col])}]', end='')
            else:
                print('[ ]', end='')
        print()
    print()
    
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
            print("\nDispenser", disp, "'s cooling rate:", rate)
            results = []
            for _ in range((100*disp)//3):
                result, *_ = start_optimisation(disp, rate)
                results.append(result)
            mean_value = np.mean(results)
            mogged_rate = 0.999995 if disp >= 5 else 0.9995
            actual_value, *_ = start_optimisation(disp, mogged_rate)
            print("Mean value:", mean_value)
            print("Actual value:", actual_value)
            print("Accuracy:", mean_value / actual_value)

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
