import tkinter as tk
from tkinter import filedialog
import tkinter.font as font
import tkinter.ttk as ttk


bg_colour = '#191919'
fg_colour = '#FFFFFF'
bg_widget_colour = '#323231'
fg_button_colour = '#323231'

width = 650
height = 350

root = tk.Tk()
root.title("Stemlight: Nether Tree Farm Rates Calculator")
root.iconbitmap('ikon.ico')
root.configure(bg=bg_colour)
root.geometry(f"{width}x{height}")

# Calculate the position of the window to center it on the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (width // 2)
y = (screen_height // 2) - (height // 2)

# Set the window position
root.geometry(f"+{x}+{y}")

main_font = font.Font(family='Segoe UI Semibold', size=11)
button_font = font.Font(family='Segoe UI Semibold', size=11)


def calculate():
    print('calculated :D')


def open_file_explorer():
    filename = filedialog.askopenfilename()
    print(filename)


# Function to create input entry boxes based on combobox selection
def create_inputs():
    # Remove any previously created input entry boxes
    for key in adv_labels:
        adv_labels[key].grid_forget()

    # Get the selected input entry name from the combobox
    selected_input = combobox.get()

    # Create the entry boxes and labels for the selected input entry
    for k in range(4):
        # Create a label for the entry box
        label_text = f"{selected_input}{k + 1}"
        label = tk.Label(root, text=label_text, bg=bg_colour, fg=fg_colour, font=main_font)
        label.grid(row=len(input_labels) + k + 1, column=0, padx=10, pady=10)

        # Store the label in the dictionary for later use
        adv_labels[k + 1] = label

        # Create an entry box for the number
        entry = tk.Entry(root, width=10)
        entry.grid(row=len(input_labels) + k + 1, column=1, padx=10, pady=10)


# Create a dictionary to store the labels
labels = {}

# Define the labels for each entry box
input_labels = ["Dispensers",
                "Dispenser Fire Frequency (gt)",
                "Hat Harvesting Frequency (gt)",
                "Trunk Harvesting Frequency (gt)",
                "Trunk Height"]

# Create the entry boxes and labels for inputs
for i, label_text in enumerate(input_labels):
    # Create a label for the entry box
    label = tk.Label(root, text=label_text, bg=bg_colour, fg=fg_colour, font=main_font)
    label.grid(row=i, column=0, padx=10, pady=10)

    # Store the label in the dictionary for later use
    labels[i + 1] = label

    # Create an entry box for the number
    entry = tk.Entry(root, width=10)
    entry.grid(row=i, column=1, padx=10, pady=10)

# Create the dropdown menu label
adv_options_label = tk.Label(root, text="Advanced Options", bg=bg_colour, fg=fg_colour, font=main_font)
adv_options_label.grid(row=len(input_labels), column=0, padx=10, pady=10)

# Create the combobox widget with the input entry names
input_entry_names = ["Layer 2 Dispensers", "Trunk Start", "C", "D"]
combobox = ttk.Combobox(root, values=input_entry_names)
combobox.grid(row=len(input_labels), column=1, padx=10, pady=10)

# Dictionary to store the advanced options input labels
adv_labels = {}

# Create a button to create the input entry boxes when the combobox is selected
adv_button = tk.Button(root, text="Create Inputs", command=create_inputs)
adv_button.grid(row=len(input_labels), column=2, padx=10, pady=10)


browse_button = tk.Button(root, text="Encoded Layout .litematic", bg='#D42121', font=button_font,
                          command=open_file_explorer)
browse_button.grid(row=len(input_labels)+1, column=0, padx=10, pady=10)

# Create the labels for outputs
output_labels = ["Stems/h",
                 "Shrooms/h",
                 "Wart Blocks/h",
                 "Bonemeal Produced/h",
                 "Bonemeal Used/h",
                 "Bonemeal Required/h",
                 "Total Drops/h"]

# Create the output labels
for i, label_text in enumerate(output_labels):
    # Create a label for the output
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=2, padx=10, pady=10)

    # Store the label in the dictionary for later use
    labels[i + 6] = label

    # Create a label for the output value
    output = tk.Label(root, text="0")
    output.grid(row=i, column=3, padx=10, pady=10)

# Create a button to calculate the outputs
calculate_button = tk.Button(root, text="Calculate!", font=button_font, command=calculate, bg="#00a7a3", fg="black")
calculate_button.grid(row=len(input_labels)+1, column=1, padx=10, pady=10)

# Create Entry widgets
dispenser_entry = tk.Entry(root, width=10, bg=bg_widget_colour, fg=fg_colour, font=main_font)
dispenser_entry.grid(row=0, column=1, padx=10, pady=10)

dispenser_fire_entry = tk.Entry(root, width=10, bg=bg_widget_colour, fg=fg_colour, font=main_font)
dispenser_fire_entry.grid(row=1, column=1, padx=10, pady=10)

hat_frequency_entry = tk.Entry(root, width=10, bg=bg_widget_colour, fg=fg_colour, font=main_font)
hat_frequency_entry.grid(row=2, column=1, padx=10, pady=10)

trunk_harvesting_entry = tk.Entry(root, width=10, bg=bg_widget_colour, fg=fg_colour, font=main_font)
trunk_harvesting_entry.grid(row=3, column=1, padx=10, pady=10)

trunk_height_entry = tk.Entry(root, width=10, bg=bg_widget_colour, fg=fg_colour, font=main_font)
trunk_height_entry.grid(row=4, column=1, padx=10, pady=10)


# Create the output labels
for i, label_text in enumerate(output_labels):
    # Create a label for the output
    label = tk.Label(root, text=label_text, bg=bg_colour, fg=fg_colour, font=main_font)
    label.grid(row=i, column=2, padx=10, pady=10)
    # Store the label in the dictionary for later use
    labels[i + 6] = label

    # Create a label for the output value
    output = tk.Label(root, text="0", bg=bg_colour, fg=fg_colour, font=main_font)
    output.grid(row=i, column=3, padx=10, pady=10)

root.mainloop()
