import tkinter as tk
import os


# Define function to open a Python file
def open_file(folder, file_name):
    os.system(f"python ../{folder}/{file_name}")


# Create main window
root = tk.Tk()
root.title("Main Menu")

# Define file names and button labels
file_names = [
    "Nether_Tree_Farm_Layout_Efficiency_Calculator.py",
    "Nether_Tree_Farm_Rates_Calculator.py",
    "Nylium_Dispenser_Placement_Calculator.py",
    "Trunk_Distribution_Calculator.py"
]
folder_names = [
    "Nether_Tree_Farm_Layout_Efficiency_Calculator",
    "Nether_Tree_Farm_Rates_Calculator",
    "Nylium_Dispenser_Placement_Calculator",
    "Trunk_Distribution_Calculator"
]
button_labels = ["Layout Efficiency", "Farm Rates", "Nylium Dispenser Placement", "Trunk Distribution"]

# Create buttons using a for loop
for i in range(len(file_names)):
    button = tk.Button(root, text=button_labels[i], command=lambda file=file_names[i], folder = folder_names[i]:
        open_file(folder, file))
    button.pack()

# Start main loop
root.mainloop()
