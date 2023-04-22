import tkinter as tk
import tkinter.font as font
import threading
import os


# Define function to open a Python file
def open_file(folder, file_name):
    os.system(f"python ../{folder}/{file_name}")


def open_file_single_instance(folder, file):
    thread = threading.Thread(target=open_file, args=(folder, file))
    thread.start()


bg_colour = '#191919'
fg_colour = '#FFFFFF'
bg_widget_colour = '#323231'
fg_button_colour = '#323231'
subheading_colour = '#FA873A'

# Create main window
root = tk.Tk()
root.title("Stemlight: Main Menu")
root.iconbitmap('../../assets/ikon.ico')
root.configure(bg=bg_colour)

# Create menu
toolbar = tk.Menu(root)
root.config(menu=toolbar)

file_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# fonts
main_font = font.Font(family='Segoe UI Semibold', size=11)
button_font = font.Font(family='Segoe UI Semibold', size=11)
subheading_font = font.Font(family='Segoe UI Semibold', size=12)

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

button_labels = [
    "Layout Efficiency",
    "Farm Rates",
    "Nylium Dispenser Placement",
    "Trunk Distribution"
]

# Create buttons using a for loop
for i in range(len(file_names)):
    button = tk.Button(root, text=button_labels[i],
                       command=lambda file=file_names[i], folder=folder_names[i]: open_file_single_instance(folder,
                                                                                                            file))
    button.config(bg=bg_colour, fg=fg_colour, font=main_font, padx=10, pady=10, width=25, height=2)
    button.grid(row=i // 2, column=i % 2, padx=5, pady=5)

# Start main loop
root.mainloop()
