import sys
import tkinter as tk
from tkinter import filedialog
import tkinter.font as font
import os

from src.Assets import colours as col, constants as const
from src.Assets.constants import RSF
from src.Assets.version import version
from src import calculate_layout

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def start(root):
    # Window padding
    PAD = int(RSF*10)
    # Non-linear scaling
    NLS = 1.765

    def set_dp(value):
        dp.set(value)

    def calculate(dispenser_value, dispenser_period_value, hat_period_value, trunk_period_value,
                trunk_height_value, layer2_dispenser_value, trunk_start_value,
                infinite_dispenser_value):
        # Dispenser, trunk and hat cycles
        trunk_cycles = max(1, trunk_period_value / dispenser_period_value)
        hat_cycles = max(1, hat_period_value / dispenser_period_value)

        # Fungus growth chance per cycle and used per hour
        if infinite_dispenser_value.lower() in const.YES_OPTIONS:
            growth_chance = 1
        else:
            growth_chance = 1 - (1 - const.FUNG_GROWTH_CHANCE) ** dispenser_value
        
        # Assuming the layer 1 stem is cleared by a separate circuit that syncs with the dispensers
        fungus = growth_chance * const.TICKS_PER_HR / dispenser_period_value

        # Schematic to layout efficiency
        layout_values = calculate_layout.schematic_to_efficiency(
            schematic_path_val.get(), hat_cycles, trunk_cycles)
        stems_per_cycle, shrooms_per_cycle, warts_per_cycle, stem_eff, shroom_eff, wart_eff = \
            layout_values[0], layout_values[1], layout_values[2], layout_values[3], layout_values[4], layout_values[5]

        # Upper bound bonemeal used per hour
        # (fraction is the bonemeal required to produce 1 crimson fungus)
        bm_used = (1 / const.FUNG_GROWTH_CHANCE + const.BM_FOR_CRMS_FUNG) * fungus

        # Stems, shroomlights and wart blocks produced per hour
        # If custom layout isn't input, default to number input for trunk properties
        # (as opposed to gathering trunk harvesting data from the layout.litematic file)
        if schematic_path_val.get() in ['']:
            stems_per_cycle = 0
            # Clamping range
            first = max(0, min(trunk_start_value, const.NT_MAX_HT))
            second = max(0, min(trunk_height_value, const.NT_MAX_HT))
            for layer in range(min(first, second) - 1, max(first, second)):
                if layer2_dispenser_value.lower() in const.YES_OPTIONS and layer == 1:
                    continue
                stems_per_cycle += const.CUML_TRUNK_DIST[layer]
            # No dispensers --> no trees grown bud
            if dispenser_value > 0:
                stem_eff = stems_per_cycle / const.AVG_STEMS
            else:
                stem_eff = 0

        if infinite_dispenser_value.lower() in const.YES_OPTIONS:
            stem_rates = fungus * stems_per_cycle
            shroom_rates = fungus * shrooms_per_cycle
            wart_rates = fungus * warts_per_cycle
        else:
            stem_rates = fungus / trunk_cycles * stems_per_cycle
            shroom_rates = fungus / hat_cycles * shrooms_per_cycle 
            wart_rates = fungus / hat_cycles * warts_per_cycle

        # Bone meal produced per hour from just wart blocks.
        # It takes 137/17 (~8.05882352941) wart blocks to make 1 bonemeal
        bm_produced = wart_rates / const.WARTS_PER_BM

        # Bone meal required per hour
        bm_required = bm_used - bm_produced

        # Accounts for stems obstructed by a second dispenser, including the edge case of
        # harvesting only layer 1 stems
        if layer2_dispenser_value.lower() in const.YES_OPTIONS and stem_rates > fungus:
            stem_rates -= fungus

        # Total production of the farm per hour
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

        # Update the output label values
        for label_num in range(0, 11):
            labels[label_num + 16]['text'] = output_value_labels[label_num]

    # Define a function to update both the string variable and the menu label
    def update_string_and_menu():
        schematic_path_val.set(open_file_explorer())
        filename2 = os.path.basename(schematic_path_val.get())  # get the filename
        name2, extension2 = os.path.splitext(filename2)  # split the filename into name and extension
        name2 = f"Selected schematic: '{name2}'"
        toolbar.entryconfig(3, label=name2)

    def open_file_explorer():
        file_path = filedialog.askopenfilename()
        child.lift()
        print(file_path)
        return file_path

    child = tk.Toplevel(root)
    child.title(f"Stemlight{version}: Nether Tree Farm Rates Calculator")
    icon_path = resource_path('src/assets/icon.ico')
    child.iconbitmap(icon_path)
    child.configure(bg=col.bg)
    child.minsize(int((RSF**1.68)*620), int((RSF**1.3)*515))

    # Get the root window's position and size
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()

    # Position the child window to the right of the root window
    child.geometry(f"+{root_x + root_width}+{root_y}")

    # Call update_idletasks to make sure widgets have been created
    child.update_idletasks()

    main_font = font.Font(family='Segoe UI', size=int((RSF**NLS)*11))
    button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*11))
    subheading_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*12))

    dp = tk.StringVar(value="1")

    toolbar = tk.Menu(child)
    child.config(menu=toolbar)

    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.quit)

    dp_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="Decimal Places", menu=dp_menu)

    for dp_row in range(1, 6):
        dp_menu.add_radiobutton(label=dp_row, variable=dp, value=dp_row,
                                command=lambda row=dp_row: set_dp(row))

    # Create a string variable to display
    schematic_path_val = tk.StringVar(value='')

    # Create a third menu to display the string variable
    third_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    filename = os.path.basename(schematic_path_val.get())  # get the filename
    name, extension = os.path.splitext(filename)  # split the filename into name and extension
    name = f"Selected schematic: '{name}'"
    toolbar.add_cascade(label=name, menu=third_menu)

    # Create a dictionary to store the labels
    labels = {}

    # Define the labels for each entry box
    input_labels = [
        "Dispensers",
        "Dispenser Fire Period (gt)",
        "Hat Harvesting Period (gt)",
        "Trunk Harvesting Period (gt)",
        "Trunk Harvesting Top Layer",
        "Advanced Options",
        "Layer 2 Dispenser",
        "Trunk Harvesting Bottom Layer",
        "Infinite Dispensers"
    ]

    # Create the labels for outputs
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

    # Create the entry boxes and labels for inputs
    for i, label_text in enumerate(input_labels):
        if i != 5:
            # Create a label for the entry box
            label = tk.Label(child, text=label_text, bg=col.bg, fg=col.fg, font=main_font)
            label.grid(row=i, column=0, padx=PAD, pady=PAD, sticky="W")

            # Create an entry box for the number
            entry = tk.Entry(child, width=PAD)
            entry.grid(row=i, column=1, padx=PAD, pady=PAD)
        else:
            label = tk.Label(child, bg=col.bg, fg=col.fg, font=main_font)
            label.grid(row=i, column=0, padx=PAD, pady=PAD)

        # Store the label in the dictionary for later use
        labels[i + 1] = label

    # Schematic file input button
    schematic_path = tk.Button(child, text="Encoded Layout .litematic", bg=col.warped, font=button_font,
                            command=lambda: update_string_and_menu())
    schematic_path.grid(row=len(input_labels), column=0, padx=PAD, pady=PAD)

    # Create a button to calculate the outputs
    calculate_button = tk.Button(child, text="Calculate!", font=button_font,
                                command=lambda: calculate(dispenser_val.get(), 
                                                        dispenser_period_val.get(),
                                                        hat_period_val.get(),
                                                        trunk_period_val.get(),
                                                        trunk_height_val.get(),
                                                        layer2_dispenser_val.get(),
                                                        trunk_start_val.get(), 
                                                        infinite_dispenser_val.get())
                                if dispenser_period_val.get() > 0 else print(
                                    "Please enter a non-zero value for dispenser period"),
                                bg=col.crimson)
    calculate_button.grid(row=len(input_labels), column=1, padx=PAD, pady=PAD)

    # Create a dictionary to store the labels
    labels = {}
    for k, label_text2 in enumerate(output_labels):
        label2 = tk.Label(child, text=label_text2, bg=col.bg, fg=col.fg, font=main_font)
        label2.grid(row=k, column=2, padx=PAD, pady=PAD, sticky="W")
        labels[k] = label2

        output = tk.Label(child, text="", bg=col.bg, fg=col.fg, font=button_font)
        output.grid(row=k, column=3, padx=PAD, pady=PAD)
        labels[k + 16] = output

    # Create entry widgets and link them to the variables
    dispenser_val = tk.DoubleVar(value=3)
    dispenser_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                            textvariable=dispenser_val)
    dispenser_entry.grid(row=0, column=1, padx=PAD, pady=PAD)

    dispenser_period_val = tk.DoubleVar(value=4)
    dispenser_period_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                        textvariable=dispenser_period_val)
    dispenser_period_entry.grid(row=1, column=1, padx=PAD, pady=PAD)

    hat_period_val = tk.DoubleVar(value=4)
    hat_period_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                textvariable=hat_period_val)
    hat_period_entry.grid(row=2, column=1, padx=PAD, pady=PAD)

    trunk_period_val = tk.DoubleVar(value=4)
    trunk_period_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                    textvariable=trunk_period_val)
    trunk_period_entry.grid(row=3, column=1, padx=PAD, pady=PAD)

    trunk_height_val = tk.IntVar(value=1)
    trunk_height_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                textvariable=trunk_height_val)
    trunk_height_entry.grid(row=4, column=1, padx=PAD, pady=PAD)

    # Creating the 'Advanced Options:' subheading
    advanced_label = tk.Label(child, text=" Advanced Options: ", bg=col.dark_orange, fg=col.fg,
                            font=subheading_font)
    advanced_label.grid(row=5, column=0, padx=PAD, pady=PAD, sticky="W")

    layer2_dispenser_val = tk.StringVar(value='0')
    layer2_dispenser_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                    textvariable=layer2_dispenser_val)
    layer2_dispenser_entry.grid(row=6, column=1, padx=PAD, pady=PAD)

    credit_label = tk.Label(child, text="Made by ncolyer", bg=col.bg_widget, fg=col.fg, font=main_font)
    credit_label.grid(row=len(input_labels) + 1, column=0, padx=PAD, pady=PAD)

    trunk_start_val = tk.IntVar(value=1)
    trunk_start_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                textvariable=trunk_start_val)
    trunk_start_entry.grid(row=7, column=1, padx=PAD, pady=PAD)

    infinite_dispenser_val = tk.StringVar(value='0')
    infinite_dispenser_entry = tk.Entry(child, width=PAD, bg=col.bg_widget, fg=col.fg, font=main_font,
                                        textvariable=infinite_dispenser_val)
    infinite_dispenser_entry.grid(row=8, column=1, padx=PAD, pady=PAD)

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    finally:
        child.mainloop()
