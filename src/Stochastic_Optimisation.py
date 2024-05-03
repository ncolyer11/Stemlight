import numpy as np

from Dispenser_Distribution_Matrix import sum_foliage_distribution

SP = [
    0.10577931226910778, 0.20149313967509574,
    0.28798973593014715, 0.3660553272880777,
    0.4997510328685407, 0.6535605838853813
]
DISP_DIST = np.array([
    [SP[0], SP[1], SP[2], SP[1], SP[0]],
    [SP[1], SP[3], SP[4], SP[3], SP[1]],
    [SP[2], SP[4], SP[5], SP[4], SP[2]],
    [SP[1], SP[3], SP[4], SP[3], SP[1]],
    [SP[0], SP[1], SP[2], SP[1], SP[0]],
])

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
    neighbor = np.copy(solution)
    index = np.random.randint(0, len(neighbor))
    neighbor[index] = 1 - neighbor[index]
    return neighbor

h_offsets = [0, 2, 0]
vk_offsets = [0, 2, 0]
offsets = [h_offsets, vk_offsets]

result = sum_foliage_distribution(offsets)

print("Initial", result)
# Example usage
initial_solution = offsets
temperature = 100.0
cooling_rate = 0.99
min_temperature = 0.01
max_iterations = 1000

best_solution = simulated_annealing(sum_foliage_distribution, initial_solution, temperature,
                                    cooling_rate, min_temperature, max_iterations)

print("Optimal offsets: ", best_solution)

