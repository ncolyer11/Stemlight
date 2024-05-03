import time
import numpy as np

from src.Fungus_Distribution_Backend import CRIMSON, calculate_fungus_distribution
from src.Dispenser_Distribution_Matrix import SIZE, foliage_distribution

def simulated_annealing(discrete_function, initial_solution, temperature, cooling_rate,
                        min_temperature, max_iterations):
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
    print(temperature, i)
    return best_solution

def acceptance_probability(current_energy, neighbor_energy, temperature):
    if neighbor_energy > current_energy:
        return 1.0
    else:
        return np.exp((neighbor_energy - current_energy) / temperature)

def generate_neighbor(solution):
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
    disp_coords = np.array(offsets) + 2
    return calculate_fungus_distribution(SIZE, SIZE, len(offsets), disp_coords, CRIMSON)[0]

def start_optimisation():
    offsets = [[2,2], [2,1], [2,0], [2,-1], [1,0], [1,-1], [1,-2], [0,-2], [0,0]]
    initial_solution = offsets
    temperature = 100.0
    cooling_rate = 0.995
    min_temperature = 0.01
    max_iterations = 10000
    
    function_choice = str(input("Select function (m/a): ")).lower()
    to_optimise_function = None
    if function_choice == "m":
        to_optimise_function = foliage_distribution
    elif function_choice == "a":
        to_optimise_function = calc_fungus_dist_wrapper
    else:
        print("Invalid function choice")
        return

    start_time = time.time()
    best_solution = simulated_annealing(to_optimise_function, initial_solution, temperature,
                                        cooling_rate, min_temperature, max_iterations)
    print("Time taken: ", time.time() - start_time)
    print("Optimal coords: \n", np.array(best_solution) + 2)
    print("Optimal value: ", to_optimise_function(best_solution))

start_optimisation()