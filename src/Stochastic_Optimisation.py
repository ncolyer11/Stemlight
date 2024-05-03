import numpy as np

from src.Dispenser_Distribution_Matrix import foliage_distribution

def simulated_annealing(discrete_function, initial_solution, temperature, cooling_rate,
                        min_temperature, max_iterations):
    current_solution = initial_solution
    best_solution = initial_solution

    for i in range(max_iterations):
        if temperature < min_temperature:
            break

        neighbor_solution = generate_neighbor(current_solution)
        current_energy = discrete_function(current_solution)
        neighbor_energy = discrete_function(neighbor_solution)
        print(i, best_solution, discrete_function(best_solution))

        if neighbor_energy > current_energy or \
           np.random.rand() < acceptance_probability(current_energy, neighbor_energy, temperature):
            current_solution = neighbor_solution
            if neighbor_energy > discrete_function(best_solution):
                best_solution = neighbor_solution

        temperature *= cooling_rate

    return best_solution

def acceptance_probability(current_energy, neighbor_energy, temperature):
    if neighbor_energy > current_energy:
        return 1.0
    else:
        return np.exp((neighbor_energy - current_energy) / temperature)

def generate_neighbor(solution):
    # Create a copy of the current solution
    neighbor_solution = solution.copy()
    # Randomly select an offset to change
    index_to_change = np.random.randint(len(solution))
    
    # Randomly select a small change in horizontal and vertical offset (-1, 0, or 1)
    new_offset = [solution[index_to_change][0] + np.random.randint(-2, 3),
                  solution[index_to_change][1] + np.random.randint(-2, 3)]  
    
    # Ensure the new offset stays within the bounds of the 5x5 nylium grid (coords centred at 0,0)
    new_offset[0] = max(-2, min(2, new_offset[0]))
    new_offset[1] = max(-2, min(2, new_offset[1]))

    # Make sure no two offsets can be the same
    while new_offset in neighbor_solution[:index_to_change] + neighbor_solution[index_to_change+1:]:
        new_offset = [solution[index_to_change][0] + np.random.randint(-2, 3),
                    solution[index_to_change][1] + np.random.randint(-2, 3)]  
        new_offset[0] = max(-2, min(2, new_offset[0]))
        new_offset[1] = max(-2, min(2, new_offset[1]))
    
    # Update the solution with the new offset
    neighbor_solution[index_to_change] = new_offset
    
    return neighbor_solution


offsets = [[2,2], [2,1]]
result = foliage_distribution(offsets)

print("Initial", result)
# Example usage
initial_solution = offsets
temperature = 100.0
cooling_rate = 0.9995
min_temperature = 0.01
max_iterations = 250

best_solution = simulated_annealing(foliage_distribution, initial_solution, temperature,
                                    cooling_rate, min_temperature, max_iterations)

print("Optimal offsets: ", best_solution)
print("Optimal value: ", foliage_distribution(best_solution))
