"""A program that outputs the efficiency and VRM count information \nfor a given encoded ntf layout schematic file"""

import tkinter as tk
from tkinter import filedialog
from tkinter import font
import os
import threading

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version
from src.Assets.helpers import resource_path, set_title_and_icon
from src.Assets.helpers import schem_layout_to_efficiency_and_vrms

def start(root):
    def set_dp(value, file_path):
        dp.set(value)
        output(file_path)

    def output(file_path):
        # Convert .litematic file to efficiency, and vrm type and quantity data
        layout_values = schem_layout_to_efficiency_and_vrms(file_path)
        avg_stems, avg_shroomlights, avg_wart_blocks, stem_E, shroomlight_E, wart_block_E, vrm0, vrm1, vrm2, vrm3 = \
            layout_values[0], layout_values[1], layout_values[2], layout_values[3], layout_values[4], layout_values[5], \
            layout_values[6], layout_values[7], layout_values[8], layout_values[9]

        d_p = int(dp.get())
        output_value_labels = [
            round(avg_stems, d_p),
            round(avg_shroomlights, d_p),
            round(avg_wart_blocks, d_p),
            f"{round(100 * stem_E, d_p)}%",
            f"{round(100 * shroomlight_E, d_p)}%",
            f"{round(100 * wart_block_E, d_p)}%",
            round(vrm0, d_p),
            round(vrm1, d_p),
            round(vrm2, d_p),
            round(vrm3, d_p)
        ]

        # update the output label values
        for label_num in range(0, 6):
            labels[label_num + 3]['text'] = output_value_labels[label_num]

        filename = os.path.basename(file_path)  # get the filename
        name, extension = os.path.splitext(filename)  # split the filename into name and extension
        labels[10].configure(text="Schematic: " + name)

        for label_num in range(0, 4):
            vrm_labels[label_num + 4]['text'] = output_value_labels[label_num + 6]

    def select_file():
        file_path = filedialog.askopenfilename()
        child.lift()
        if file_path:
            threading.Thread(target=output, args=(file_path,)).start()
            return file_path

    child = tk.Toplevel(root)
    set_title_and_icon(child, "Nether Tree Farm Layout Efficiency Calculator")

    child.configure(bg=colours.bg)

    # Get the root window's position and size
    root_x = root.winfo_x()
    root_y = root.winfo_rooty()
    root_height = root.winfo_height()

    # Position the child window to the right of the root window
    child.geometry(f"+{root_x}+{root_y + root_height}")

    # Update the window so it actually appears in the correct position
    child.update_idletasks()

    dp = tk.StringVar(value="2")

    toolbar = tk.Menu(child)
    child.config(menu=toolbar)

    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.destroy)

    dp_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="Decimal Places", menu=dp_menu)

    for dp_row in range(1, 6):
        dp_menu.add_radiobutton(label=dp_row, variable=dp, value=dp_row, command=lambda row=dp_row: set_dp(row, path.get()))

    main_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*12))
    output_font = font.Font(family='Segoe UI', size=int((RSF**1.765)*11))
    subheading_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*12))

    button = tk.Button(child, text="Select Schematic", bg=colours.warped, font=main_font,
                    command=lambda: path.set(select_file()))
    button.grid(row=0, column=1, pady=15)

    path = tk.StringVar()

    labels = {}
    # define block types
    output_labels = [
        "    Stems    ",
        " Shroomlights" if RSF == 1 else " Shroomlights ",
        " Wart Blocks "
    ]

    for i, output_label in enumerate(output_labels):
        label = tk.Label(child, text=output_label, bg=colours.dark_orange, fg=colours.fg, font=main_font)
        label.grid(row=1, column=i)
        labels[i] = label  # add the label to the dictionary with key 'i'

        value_label = tk.Label(child, text="", bg=colours.bg, fg=colours.fg, font=output_font)
        value_label.grid(row=2, column=i)
        labels[i + 3] = value_label  # add the output label to the dictionary with key 'i+3'
        value_label = tk.Label(child, text="", bg=colours.bg, fg=colours.fg, font=output_font)
        value_label.grid(row=3, column=i)
        labels[i + 6] = value_label  # add the output label to the dictionary with key 'i+3'

    schematic_display = tk.Frame(child)
    schematic_display.grid(row=7, column=1)
    schematic_display.configure(bg=colours.bg)

    schematic_label = tk.Label(schematic_display, text="Schematic: ", bg=colours.bg, fg=colours.fg,
                            font=main_font)
    schematic_label.grid(row=0, column=0)
    labels[10] = schematic_label

    vrm_labels = {}

    # function to create a new 2x4 grid of values
    vrms_labels = [
        "vrm0's",
        "vrm1's",
        "vrm2's",
        "vrm3's"
    ]

    # create a new frame for the vrms grid
    vrms_frame = tk.Frame(child)
    vrms_frame.grid(row=6, column=0, columnspan=3)
    vrms_frame.configure(bg=colours.bg)

    for j, val2 in enumerate(vrms_labels):
        label2 = tk.Label(vrms_frame, text=val2, width=10, bg=colours.dark_blue_grey, fg=colours.fg, font=main_font)
        label2.grid(row=0, column=j)
        vrm_labels[j] = label2

        label2 = tk.Label(vrms_frame, text="", bg=colours.bg, fg=colours.fg, font=output_font)
        label2.grid(row=1, column=j)
        vrm_labels[j + 4] = label2

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    child.mainloop()
