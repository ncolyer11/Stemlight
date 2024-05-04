import time
import numpy as np

from Fast_Dispenser_Distribution import fast_calculate_distribution
from src.Dispenser_Distribution_Matrix import SIZE, foliage_distribution

ACCEPTANCE_RATE = 0.995

def simulated_annealing(discrete_function, initial_solution, temperature, cooling_rate,
                        min_temperature, max_iterations):
    """Simulated annealing algorithm for discrete optimisation problems."""
    current_solution = initial_solution
    best_solution = initial_solution
    i = 0
    for i in range(max_iterations):
        if temperature < min_temperature:
            break
        neighbor_solution = generate_neighbor(current_solution)
        current_energy = discrete_function(current_solution)
        neighbor_energy = discrete_function(neighbor_solution)

        if neighbor_energy > current_energy or \
           np.random.rand() < acceptance_probability(current_energy, neighbor_energy, temperature):
            current_solution = neighbor_solution
            if neighbor_energy > discrete_function(best_solution):
                best_solution = neighbor_solution

        temperature *= cooling_rate
    print("End temperature:", temperature, "Iterations:", i)
    return best_solution

def acceptance_probability(current_energy, neighbor_energy, temperature):
    """Calculate the probability of accepting a worse solution."""
    if neighbor_energy > current_energy:
        return 1.0
    else:
        return np.exp((neighbor_energy - current_energy) / temperature)

def generate_neighbor(solution):
    """Generate a new dispenser permutation by altering 1 to all of their offsets slightly"""
    # Create a copy of the current solution
    neighbor_solution = solution.copy()
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
        while new_offset in neighbor_solution[:index_to_change] + neighbor_solution[index_to_change+1:]:
            new_offset = [solution[index_to_change][0] + np.random.randint(-1, 2),
                        solution[index_to_change][1] + np.random.randint(-1, 2)]  
            new_offset[0] = max(-2, min(2, new_offset[0]))
            new_offset[1] = max(-2, min(2, new_offset[1]))
    
    # Update the solution with the new offset
    neighbor_solution[index_to_change] = new_offset
    
    return neighbor_solution

def calc_fungus_dist_wrapper(offsets):
    """Wrapper for the fungus distribution function to allow it to be used in 
    the optimisation algorithm."""
    disp_coords = np.array(offsets) + 2
    return fast_calculate_distribution(SIZE, SIZE, disp_coords)

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

def calculate_start_temp(N, function):
    """Calculate the starting temperature for the simulated annealing algorithm."""
    # Generate a random initial solution
    initial_solution = [[np.random.randint(-2, 3), np.random.randint(-2, 3)] for _ in range(N)]
    # Calculate the average energy of the initial solution
    avg_energy = np.mean([function(initial_solution) for _ in range(100)])
    # Calculate the average energy of the initial solution with a small change
    avg_energy_change = np.mean([function(generate_neighbor(initial_solution)) for _ in range(100)])
    # Calculate the starting temperature
    start_temperature = -avg_energy / np.log(ACCEPTANCE_RATE)
    print("Start temperature:", start_temperature)
    print("Average energy change:", avg_energy_change - avg_energy)
    return start_temperature

def start_optimisation():
    """Start optimising the function using the simulated annealing algorithm."""
    num_dispensers = int(input("Enter number of dispensers: "))
    function_choice = str(input("Select function (m/a): ")).lower()
    to_optimise_function = None
    if function_choice == "m":
        to_optimise_function = foliage_distribution
    elif function_choice == "a":
        to_optimise_function = calc_fungus_dist_wrapper
    else:
        print("Invalid function choice")
        return
    
    offsets = [[0,0] for _ in range(num_dispensers)] 
    initial_solution = offsets
    start_temperature = calculate_start_temp(num_dispensers, to_optimise_function)
    cooling_rate = 0.9995
    min_temperature = 1e-4
    max_iterations = 10000000
    

    start_time = time.time()
    best_solution = simulated_annealing(to_optimise_function, initial_solution, start_temperature,
                                        cooling_rate, min_temperature, max_iterations)
    output_results(to_optimise_function, best_solution, start_time)

start_optimisation()