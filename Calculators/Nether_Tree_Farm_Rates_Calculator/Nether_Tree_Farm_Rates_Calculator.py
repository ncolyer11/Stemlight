import tkinter as tk
from tkinter import filedialog
import tkinter.font as font
import os

from Assets import colours
import calculate_layout

root = tk.Tk()
root.title("Stemlight: Nether Tree Farm Rates Calculator")
root.iconbitmap('../Assets/ikon.ico')
root.configure(bg=colours.bg)

# call update_idletasks to make sure widgets have been created
root.update_idletasks()
width = root.winfo_reqwidth()
height = root.winfo_reqheight()

# calculate the position of the window to center it on the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - 2 * width
y = (screen_height // 2) - round(3 * height / 2)

# set the window position
root.geometry(f"+{x}+{y}")

main_font = font.Font(family='Segoe UI', size=11)
button_font = font.Font(family='Segoe UI Semibold', size=11)
subheading_font = font.Font(family='Segoe UI Semibold', size=12)

dp = tk.StringVar(value="0")


def set_dp(value):
    dp.set(value)


toolbar = tk.Menu(root)
root.config(menu=toolbar)

file_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

dp_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="Decimal Places", menu=dp_menu)

for dp_row in range(0, 6):
    dp_menu.add_radiobutton(label=dp_row, variable=dp, value=dp_row,
                            command=lambda row=dp_row: set_dp(row))

# Create a string variable to display
schematic_path_val = tk.StringVar(value="../Assets/empty_layout.litematic")

# Create a third menu to display the string variable
third_menu = tk.Menu(toolbar, tearoff=0)
filename = os.path.basename(schematic_path_val.get())  # get the filename
name, extension = os.path.splitext(filename)  # split the filename into name and extension
name = f"Selected schematic: '{name}'"
toolbar.add_cascade(label=name, menu=third_menu)


def calculate(dispenser_value, dispenser_frequency_value, hat_frequency_value, trunk_frequency_value,
              trunk_height_value, layer2_dispenser_value, trunk_start_value, infinite_dispenser_value):
    yes_options = {'y', 'yes', 'on', '1'}

    # huge fungus related constants
    fungus_growth_chance = 0.4
    trunk_distribution = 7 * [1 / 120, 0] + 3 * [11 / 120, 0.1] + 4 * [11 / 120] + 3 * [0.0]
    cumulative_trunk_distribution = [0.0] * (len(trunk_distribution) + 1)
    for index in range(1, len(cumulative_trunk_distribution)):
        cumulative_trunk_distribution[index] = (cumulative_trunk_distribution[index - 1] +
                                                trunk_distribution[index - 1])
    # reversing the order of the list
    cumulative_trunk_distribution = cumulative_trunk_distribution[::-1]

    # dispenser, trunk and hat cycles
    hourly_cycles = 72000 / dispenser_frequency_value
    trunk_cycles = max(1, trunk_frequency_value / dispenser_frequency_value)
    hat_cycles = max(1, hat_frequency_value / dispenser_frequency_value)

    # schematic to layout efficiency
    layout_values = calculate_layout.schematic_to_efficiency(schematic_path_val.get(), hat_cycles, trunk_cycles)
    stems_per_cycle, shrooms_per_cycle, warts_per_cycle, stem_eff, shroom_eff, wart_eff = \
        layout_values[0], layout_values[1], layout_values[2], layout_values[3], layout_values[4], layout_values[5]

    # fungus growth chance per cycle
    if infinite_dispenser_value.lower() in yes_options:
        growth_chance = 1
    else:
        growth_chance = 1 - (1 - fungus_growth_chance) ** dispenser_value

    # fungus used per hour
    fungus = growth_chance * hourly_cycles

    # upper bound bonemeal used per hour (fraction is bonemeal required to produce 1 crimson fungus)
    bm_used = (1 / fungus_growth_chance + (18000 - 11423) / 14608) * fungus

    # stems, shroomlights and wart blocks produced per hour
    if schematic_path_val.get() == '../Assets/empty_layout.litematic':
        stems_per_cycle = 0
        layer = trunk_start_value - 1
        while layer < trunk_height_value:
            stems_per_cycle += cumulative_trunk_distribution[layer]
            layer += 1

    stem_rates = fungus / trunk_cycles * stems_per_cycle
    shroom_rates, wart_rates = fungus / hat_cycles * shrooms_per_cycle, fungus / hat_cycles * warts_per_cycle

    # bonemeal produced per hour from just wart blocks. it takes 137/17 (~8.05882352941) wart blocks to make 1 bonemeal
    bm_produced = wart_rates * 17 / 137

    # bonemeal required per hour
    bm_required = bm_used - bm_produced

    # accounts for stems obstructed by a second dispenser, including the edge case of harvesting only layer 1 stems
    if layer2_dispenser_value.lower() in yes_options and stem_rates > fungus:
        stem_rates -= fungus

    # total production of the farm per hour
    total_rates = stem_rates + shroom_rates + wart_rates

    d_p = int(dp.get())
    output_value_labels = [
        f"{round(stem_rates, d_p)}",
        f"{round(shroom_rates, d_p)}",
        f"{round(wart_rates, d_p)}",
        f"{round(fungus, d_p)}",
        f"{round(bm_produced, d_p)}",
        f"{round(bm_used, d_p)}",
        f"{round(bm_required, d_p)}",
        f"{round(100 * stem_eff, d_p)}%",
        f"{round(100 * shroom_eff, d_p)}%",
        f"{round(100 * wart_eff, d_p)}%",
        f"{round(total_rates, d_p)}"
    ]

    # update the output label values
    for label_num in range(0, 11):
        labels[label_num + 16]['text'] = output_value_labels[label_num]


# Define a function to update both the string variable and the menu label
def update_string_and_menu():
    schematic_path_val.set(open_file_explorer())
    filename = os.path.basename(schematic_path_val.get())  # get the filename
    name, extension = os.path.splitext(filename)  # split the filename into name and extension
    name = f"Selected schematic: '{name}'"
    toolbar.entryconfig(3, label=name)


def open_file_explorer():
    file_path = filedialog.askopenfilename()
    print(file_path)
    return file_path


# create a dictionary to store the labels
labels = {}

# define the labels for each entry box
input_labels = [
    "Dispensers",
    "Dispenser Fire Frequency (gt)",
    "Hat Harvesting Frequency (gt)",
    "Trunk Harvesting Frequency (gt)",
    "Trunk Harvesting Top Layer",
    "Advanced Options",
    "Layer 2 Dispenser",
    "Trunk Harvesting Bottom Layer",
    "Infinite Dispensers"
]

# create the entry boxes and labels for inputs
for i, label_text in enumerate(input_labels):
    if i != 5:
        # create a label for the entry box
        label = tk.Label(root, text=label_text, bg=colours.bg, fg=colours.fg, font=main_font)
        label.grid(row=i, column=0, padx=10, pady=10, sticky="W")

        # create an entry box for the number
        entry = tk.Entry(root, width=10)
        entry.grid(row=i, column=1, padx=10, pady=10)
    else:
        label = tk.Label(root, bg=colours.bg, fg=colours.fg, font=main_font)
        label.grid(row=i, column=0, padx=10, pady=10)

    # store the label in the dictionary for later use
    labels[i + 1] = label

# in the future make it so the file input button text changes to the current inputted schematic
schematic_path = tk.Button(root, text="Encoded Layout .litematic", bg=colours.warped, font=button_font,
                           command=lambda: update_string_and_menu())
schematic_path.grid(row=len(input_labels), column=0, padx=10, pady=10)

# create a button to calculate the outputs
calculate_button = tk.Button(root, text="Calculate!", font=button_font,
                             command=lambda: calculate(dispenser_val.get(), dispenser_frequency_val.get(),
                                                       hat_frequency_val.get(), trunk_frequency_val.get(),
                                                       trunk_height_val.get(), layer2_dispenser_val.get(),
                                                       trunk_start_val.get(), infinite_dispenser_val.get())
                             if dispenser_frequency_val.get() > 0 else print("Please enter a non-zero value for"
                                                                             " dispenser frequency"),
                             bg=colours.crimson)
calculate_button.grid(row=len(input_labels), column=1, padx=10, pady=10)

# create the labels for outputs
output_labels = [
    "Stems/h",
    "Shrooms/h",
    "Wart Blocks/h",
    "Fungus Used/h",
    "Bonemeal Produced/h",
    "Bonemeal Used/h",
    "Bonemeal Required/h",
    "Stem Efficiency",
    "Shroomlight Efficiency",
    "Wart Block Efficiency",
    "Total Drops/h"
]

# create a dictionary to store the labels
labels = {}
for k, label_text2 in enumerate(output_labels):
    label2 = tk.Label(root, text=label_text2, bg=colours.bg, fg=colours.fg, font=main_font)
    label2.grid(row=k, column=2, padx=10, pady=10, sticky="W")
    labels[k] = label2

    output = tk.Label(root, text="", bg=colours.bg, fg=colours.fg, font=button_font)
    output.grid(row=k, column=3, padx=10, pady=10)
    labels[k + 16] = output

# create entry widgets and link them to the variables
dispenser_val = tk.IntVar(value=3)
dispenser_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                           textvariable=dispenser_val)
dispenser_entry.grid(row=0, column=1, padx=10, pady=10)

dispenser_frequency_val = tk.IntVar(value=4)
dispenser_frequency_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                                     textvariable=dispenser_frequency_val)
dispenser_frequency_entry.grid(row=1, column=1, padx=10, pady=10)

hat_frequency_val = tk.IntVar(value=4)
hat_frequency_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                               textvariable=hat_frequency_val)
hat_frequency_entry.grid(row=2, column=1, padx=10, pady=10)

trunk_frequency_val = tk.IntVar(value=4)
trunk_frequency_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                                 textvariable=trunk_frequency_val)
trunk_frequency_entry.grid(row=3, column=1, padx=10, pady=10)

trunk_height_val = tk.IntVar(value=1)
trunk_height_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                              textvariable=trunk_height_val)
trunk_height_entry.grid(row=4, column=1, padx=10, pady=10)

# creating the 'Advanced Options:' subheading
advanced_label = tk.Label(root, text=" Advanced Options: ", bg=colours.dark_orange, fg=colours.fg,
                          font=subheading_font)
advanced_label.grid(row=5, column=0, padx=10, pady=10, sticky="W")

layer2_dispenser_val = tk.StringVar(value='0')
layer2_dispenser_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                                  textvariable=layer2_dispenser_val)
layer2_dispenser_entry.grid(row=6, column=1, padx=10, pady=10)

credit_label = tk.Label(root, text="Made by ncolyer", bg=colours.bg_widget, fg=colours.fg, font=main_font)
credit_label.grid(row=len(input_labels) + 1, column=0, padx=10, pady=10)

trunk_start_val = tk.IntVar(value=1)
trunk_start_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                             textvariable=trunk_start_val)
trunk_start_entry.grid(row=7, column=1, padx=10, pady=10)

infinite_dispenser_val = tk.StringVar(value='0')
infinite_dispenser_entry = tk.Entry(root, width=10, bg=colours.bg_widget, fg=colours.fg, font=main_font,
                                    textvariable=infinite_dispenser_val)
infinite_dispenser_entry.grid(row=8, column=1, padx=10, pady=10)

root.mainloop()
