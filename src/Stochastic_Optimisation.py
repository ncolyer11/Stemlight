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
    # Randomly select an offset to change
    index_to_change = np.random.randint(len(solution))
    
    # Randomly select a new offset with a small deviation from the current one
    new_offset = [solution[index_to_change][0] + np.random.randint(-1, 2),  # Random change in horizontal offset (-1, 0, or 1)
                  solution[index_to_change][1] + np.random.randint(-1, 2)]  # Random change in vertical offset (-1, 0, or 1)
    
    # Ensure the new offset stays within the bounds of the nylium grid
    new_offset[0] = max(0, min(4, new_offset[0]))  # Clamp horizontal offset between 0 and 4
    new_offset[1] = max(0, min(4, new_offset[1]))  # Clamp vertical offset between 0 and 4
    
    # Update the solution with the new offset
    neighbor_solution = solution.copy()
    neighbor_solution[index_to_change] = new_offset
    
    return neighbor_solution


offsets = [[0,0], [1,1]]
result = foliage_distribution(offsets)

print("Initial", result)
# Example usage
initial_solution = offsets
temperature = 100.0
cooling_rate = 0.99
min_temperature = 0.01
max_iterations = 1000

best_solution = simulated_annealing(foliage_distribution, initial_solution, temperature,
                                    cooling_rate, min_temperature, max_iterations)

print("Optimal offsets: ", best_solution)
