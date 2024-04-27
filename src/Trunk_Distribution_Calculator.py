"""Calculates the number of stems and stem efficiency for a given trunk distribution."""

import tkinter as tk
import tkinter.font as font
from tkinter import Menu

from src.Assets import colours as cols, constants as const
from src.Assets.constants import RSF
from src.Assets.version import version
from src.Assets.helpers import resource_path


def start(root):
    PAD = int(RSF*10)

    def set_dp(value):
        dp.set(value)

    def calculate_stem_efficiency(first, second, second_layer_dispenser):
        # clamp values between 0 and 27 (inclusive)
        first = max(0, min(first, const.NT_MAX_HT))
        second = max(0, min(second, const.NT_MAX_HT))
        stems = 0
        for layer in range(min(first, second) - 1, max(first, second)):
            if second_layer_dispenser.lower() in const.YES_OPTIONS and layer == 1:
                continue
            stems += const.CUML_TRUNK_DIST[layer]
        
        
        stem_efficiency = stems / const.AVG_STEMS
        d_p = int(dp.get())
        return f"{round(stems, d_p)}", f"{round(100 * stem_efficiency, d_p)}"

    def calculate_and_display(first_val_var, second_val_var, result_label, dispenser_value_var):
        first = int(first_val_var.get())
        second = int(second_val_var.get())
        dispenser = dispenser_value_var.get()
        stems, stem_efficiency = calculate_stem_efficiency(first, second, dispenser)
        
        result_text = f"Stems per Cycle: {stems}\nStem Efficiency: {stem_efficiency}%"
        result_label.config(text=result_text)

    # Create the main tkinter window
    child = tk.Toplevel(root)
    child.title(f"Stemlight{version}: Trunk Distribution Calculator")
    try:
        # Try to use the .ico file
        icon_path = resource_path('src/Assets/icon.ico')
        child.iconbitmap(icon_path)
    except:
        # If that fails, try to use the .xbm file
        try:
            icon_path = resource_path('src/Assets/icon.xbm')
            child.iconbitmap('@' + icon_path)
        except:
            pass  # If that also fails, do nothing
    child.configure(bg=cols.bg)

    root_x = root.winfo_x()
    root_y = root.winfo_rooty()
    root_width= root.winfo_width()
    root_height = root.winfo_height()

    child.geometry(f"+{root_x + root_width}+{root_y + root_height}")

    # Call update_idletasks to make sure widgets have been created
    child.update_idletasks()

    # Create a menu bar
    toolbar = Menu(child)
    child.config(menu=toolbar)

    # Create a "File" menu
    file_menu = Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.destroy)

    # Create a "Decimal Places" menu
    dp_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="Decimal Places", menu=dp_menu)
    dp = tk.StringVar(value="2")

    for dp_row in range(1, 6):
        dp_menu.add_radiobutton(label=dp_row, variable=dp, value=dp_row,
                                command=lambda row=dp_row: set_dp(row))

    main_font = font.Font(family='Segoe UI', size=int((RSF**1.765)*11))

    # Create input fields and labels
    trunk_start_label = tk.Label(child, text="From Layer:", bg=cols.bg, fg=cols.fg, font=main_font)
    trunk_start_label.grid(row=0, column=0, padx=PAD, pady=PAD, sticky="W")

    trunk_start_value_var = tk.StringVar(value="1")
    trunk_start_entry = tk.Entry(child, textvariable=trunk_start_value_var, bg=cols.bg_widget, 
                                fg=cols.fg, font=main_font)
    trunk_start_entry.grid(row=0, column=1, padx=PAD, pady=PAD)

    trunk_height_label = tk.Label(child, text="...To Layer:", bg=cols.bg, fg=cols.fg, 
                                font=main_font)
    trunk_height_label.grid(row=1, column=0, padx=PAD, pady=PAD, sticky="W")

    trunk_height_value_var = tk.StringVar(value="1")
    trunk_height_entry = tk.Entry(child, textvariable=trunk_height_value_var, bg=cols.bg_widget, 
                                fg=cols.fg, font=main_font)
    trunk_height_entry.grid(row=1, column=1, padx=PAD, pady=PAD)

    dispenser_start_label = tk.Label(child, text="2nd Layer Dispenser:", bg=cols.bg, fg=cols.fg, font=main_font)
    dispenser_start_label.grid(row=2, column=0, padx=PAD, pady=PAD, sticky="W")

    dispenser_value_var = tk.StringVar(value='0')
    dispenser_start_entry = tk.Entry(child, textvariable=dispenser_value_var, bg=cols.bg_widget, 
                                fg=cols.fg, font=main_font)
    dispenser_start_entry.grid(row=2, column=1, padx=PAD, pady=PAD)


    calculate_button = tk.Button(child, 
                                text="Calculate",
                                command=lambda: calculate_and_display(trunk_start_value_var,
                                                                    trunk_height_value_var, 
                                                                    result_label,
                                                                    dispenser_value_var), 
                                bg=cols.crimson, fg=cols.bg, font=main_font)
    calculate_button.grid(row=3, column=0, columnspan=2, pady=2*PAD)

    # Create a label for displaying results
    result_label = tk.Label(child, text="", bg=cols.bg, fg=cols.fg, font=main_font)
    result_label.grid(row=4, column=0, columnspan=2, pady=(0, 2*PAD))

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    child.mainloop()
