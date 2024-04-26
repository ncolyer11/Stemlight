from Assets import colours as cols, constants as const
import tkinter as tk
import tkinter.font as font
from tkinter import Menu, Checkbutton

from Assets.constants import RSF


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
root = tk.Tk()
root.title("Stemlight: Trunk Distribution Calculator")
root.iconbitmap('./Assets/ikon.ico')
root.configure(bg=cols.bg)

# Create a menu bar
toolbar = Menu(root)
root.config(menu=toolbar)

# Create a "File" menu
file_menu = Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# Create a "Decimal Places" menu
dp_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
toolbar.add_cascade(label="Decimal Places", menu=dp_menu)
dp = tk.StringVar(value="2")

for dp_row in range(1, 6):
    dp_menu.add_radiobutton(label=dp_row, variable=dp, value=dp_row,
                            command=lambda row=dp_row: set_dp(row))

main_font = font.Font(family='Segoe UI', size=int((RSF**1.765)*11))

# Create input fields and labels
trunk_start_label = tk.Label(root, text="From Layer:", bg=cols.bg, fg=cols.fg, font=main_font)
trunk_start_label.grid(row=0, column=0, padx=PAD, pady=PAD, sticky="W")

trunk_start_value_var = tk.StringVar(value="1")
trunk_start_entry = tk.Entry(root, textvariable=trunk_start_value_var, bg=cols.bg_widget, 
                             fg=cols.fg, font=main_font)
trunk_start_entry.grid(row=0, column=1, padx=PAD, pady=PAD)

trunk_height_label = tk.Label(root, text="...To Layer:", bg=cols.bg, fg=cols.fg, 
                              font=main_font)
trunk_height_label.grid(row=1, column=0, padx=PAD, pady=PAD, sticky="W")

trunk_height_value_var = tk.StringVar(value="1")
trunk_height_entry = tk.Entry(root, textvariable=trunk_height_value_var, bg=cols.bg_widget, 
                              fg=cols.fg, font=main_font)
trunk_height_entry.grid(row=1, column=1, padx=PAD, pady=PAD)

dispenser_start_label = tk.Label(root, text="2nd Layer Dispenser:", bg=cols.bg, fg=cols.fg, font=main_font)
dispenser_start_label.grid(row=2, column=0, padx=PAD, pady=PAD, sticky="W")

dispenser_value_var = tk.StringVar(value='0')
dispenser_start_entry = tk.Entry(root, textvariable=dispenser_value_var, bg=cols.bg_widget, 
                             fg=cols.fg, font=main_font)
dispenser_start_entry.grid(row=2, column=1, padx=PAD, pady=PAD)


calculate_button = tk.Button(root, 
                             text="Calculate",
                             command=lambda: calculate_and_display(trunk_start_value_var,
                                                                   trunk_height_value_var, 
                                                                   result_label,
                                                                   dispenser_value_var), 
                             bg=cols.crimson, fg=cols.bg, font=main_font)
calculate_button.grid(row=3, column=0, columnspan=2, pady=2*PAD)

# Create a label for displaying results
result_label = tk.Label(root, text="", bg=cols.bg, fg=cols.fg, font=main_font)
result_label.grid(row=4, column=0, columnspan=2, pady=(0, 2*PAD))

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
finally:
    root.mainloop()
