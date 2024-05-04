import time
import numpy as np
import pandas as pd

from Fast_Dispenser_Distribution import fast_calculate_distribution
from src.Dispenser_Distribution_Matrix import SIZE

ACCEPTANCE_RATE = 0.995
REJECTION_POINT = 0.1

def simulated_annealing(discrete_function, initial_solution, temperature, cooling_rate,
                        min_temperature, max_iterations):
    """Simulated annealing algorithm for discrete optimisation problems."""
    current_solution = initial_solution
    best_solution = initial_solution
    i = 0
    for i in range(max_iterations):
        if temperature < min_temperature:
            break
        neighbour_solution = generate_neighbour(current_solution)
        current_energy = discrete_function(current_solution)
        neighbour_energy = discrete_function(neighbour_solution)

        if neighbour_energy > current_energy or \
           np.random.rand() < acceptance_probability(current_energy, neighbour_energy, temperature):
            current_solution = neighbour_solution
            if neighbour_energy > discrete_function(best_solution):
                best_solution = neighbour_solution

        temperature *= cooling_rate
    # print("End temperature:", temperature, "Iterations:", i)
    return best_solution

def acceptance_probability(current_energy, neighbour_energy, temperature):
    """Calculate the probability of accepting a worse solution."""
    if neighbour_energy > current_energy:
        return 1.0
    else:
        return np.exp((neighbour_energy - current_energy) / temperature)

def generate_neighbour(solution):
    """Generate a new dispenser permutation by altering 1 to all of their offsets slightly"""
    # Create a copy of the current solution
    neighbour_solution = solution.copy()
    # Randomly select offsets to change
    indexes_to_change = np.random.choice(len(solution), len(solution), replace=False)
    for index_to_change in indexes_to_change:
        # Randomly select a small change in horizontal and vertical offset (-1, 0, or 1)
        new_offset = [solution[index_to_change][0] + np.random.randint(-1, 2),
                    solution[index_to_change][1] + np.random.randint(-1, 2)]  
        
        # Ensure the new offset stays within the bounds of the 5x5 nylium grid (coords centred at 0,0)
        new_offset[0] = max(-2, min(2, new_offset[0]))
        new_offset[1] = max(-2, min(2, new_offset[1]))

        # Make sure no two offsets can be the same
        while new_offset in neighbour_solution[:index_to_change] + neighbour_solution[index_to_change+1:]:
            # print(neighbour_solution, "\n", new_offset)
            new_offset = [solution[index_to_change][0] + np.random.randint(-2, 3),
                        solution[index_to_change][1] + np.random.randint(-2, 3)]  
            new_offset[0] = max(-2, min(2, new_offset[0]))
            new_offset[1] = max(-2, min(2, new_offset[1]))
    
    # Update the solution with the new offset
    neighbour_solution[index_to_change] = new_offset
    
    return neighbour_solution

def calc_fungus_dist_wrapper(offsets):
    """Wrapper for the fungus distribution function to allow it to be used in 
    the optimisation algorithm."""
    disp_coords = np.array(offsets) + 2
    return fast_calculate_distribution(SIZE, SIZE, disp_coords)

def calculate_temp_bounds(N, function):
    """Calculate the starting temperature for the simulated annealing algorithm."""
    # Find the lowest energy point
    lowest_energy = function([[np.random.randint(-2, -1), np.random.randint(-2, -1)] for _ in range(N)])
    # Create a valid set of offsets by passing it through generate_neighbour
    average_solutions = []
    for _ in range(300*N):
        offsets = [[np.random.randint(-2, 3),np.random.randint(-2, 3)] for _ in range(N)] 
        average_solutions.append(
            generate_neighbour(offsets)
        )
    
    # Calculate the average energy of the initial solution
    avg_energy = np.mean([function(average_solutions[i]) for i in range(len(average_solutions))])
    high_energy_change = avg_energy - lowest_energy
    
    start_temperature = -high_energy_change / np.log(ACCEPTANCE_RATE)
    end_temperature = -high_energy_change / np.log(REJECTION_POINT)
    # print("Lowest energy:", lowest_energy)
    # print("Average energy:", avg_energy)
    # print("Average worst case energy change:", high_energy_change)
    # print("Start temperature:", start_temperature)
    # print("End temperature:", end_temperature)
    return start_temperature, end_temperature, lowest_energy, avg_energy

def output_results(function, solution, start_time):
    """Output the results of the optimisation."""
    print("Time taken:", time.time() - start_time)
    best_coords = np.array(solution) + 2
    print("Optimal coords: \n", best_coords)
    print("Optimal value: ", function(solution))
        # Print the location of max_rates_coords in a grid on terminal
    for row in range(SIZE):
        for col in range(SIZE):
            if [row - 2, col - 2] in solution:
                print(f'[{solution.index([row - 2, col - 2])}]', end='')
            else:
                print('[ ]', end='')
        print()
    print()
    
def run_optimisation():
    """Run the optimisation for 1 to 10 dispensers and write the results to an Excel file."""
    results = pd.DataFrame(columns=["Num_Dispensers", "Lowest_Energy",
                                    "Average_Energy", "Start_Temperature"])

    for num_dispensers in range(1, 11):
        start_temperature, end_temperature, lowest_energy, avg_energy = \
            calculate_temp_bounds(num_dispensers, calc_fungus_dist_wrapper)
        results = pd.concat([results, pd.DataFrame([{
            "Num_Dispensers": num_dispensers, 
            "Lowest_Energy": lowest_energy, 
            "Average_Energy": avg_energy, 
            "Start_Temperature": start_temperature,
            "End_Temperature": end_temperature}], index=[0])], ignore_index=True)

    results.to_excel("optimisation_results.xlsx", index=False)

def plot_cooling_rate_data():
    """Analyse how different cooling rates affect accuracy using plotted emperical data."""
    num_dispensers = [3,4,5,6]
    cooling_rates = [0.85,0.925,0.95,0.9725,0.995,0.999]
    function_choice = calc_fungus_dist_wrapper

    # Create a DataFrame to store the results
    df = pd.DataFrame(columns=["Num_Dispensers", "Cooling_Rate", "Mean_Value", 
                               "Actual_Value", "Accuracy"])

    for disp in num_dispensers:
        for rate in cooling_rates:
            print("\nDispenser", disp, "'s cooling rate:", rate)
            results = []
            for _ in range((100*disp)//3):
                result = start_optimisation(disp, function_choice, rate)
                results.append(result)
            mean_value = np.mean(results)
            mogged_rate = 0.99995 if disp >= 5 else 0.9995
            actual_value = start_optimisation(disp, function_choice, mogged_rate)
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

def start_optimisation(num_dispensers, func_to_optimise, cooling_rate):
    """Start optimising the function using the simulated annealing algorithm."""
    offsets = [[0,0] for _ in range(num_dispensers)] 
    initial_solution = offsets
    start_temperature, end_temperature, *_ = calculate_temp_bounds(num_dispensers, func_to_optimise)
    min_temperature = end_temperature
    max_iterations = 100000

    start_time = time.time()
    best_solution = simulated_annealing(func_to_optimise, initial_solution, start_temperature,
                                        cooling_rate, min_temperature, max_iterations)
    # output_results(func_to_optimise, best_solution, start_time)
    return func_to_optimise(best_solution)

if __name__ == "__main__":
    plot_cooling_rate_data()