import tkinter as tk
from tkinter import filedialog
from tkinter import font
import os

from Assets import colours
import calculate_layout_efficiency

root = tk.Tk()
root.title("Stemlight: Nether Tree Farm Layout Efficiency Calculator")
root.iconbitmap('./Assets/ikon.ico')
root.configure(bg=colours.bg)

dp = tk.StringVar(value="2")


def set_dp(value, file_path):
    dp.set(value)
    output(file_path)


toolbar = tk.Menu(root)
root.config(menu=toolbar)

file_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

dp_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="Decimal Places", menu=dp_menu)

for dp_row in range(0, 11):
    dp_menu.add_radiobutton(label=dp_row, variable=dp, value=dp_row, command=lambda row=dp_row: set_dp(row, path.get()))

main_font = font.Font(family='Segoe UI Semibold', size=12)
output_font = font.Font(family='Segoe UI', size=11)
subheading_font = font.Font(family='Segoe UI Semibold', size=12)


def output(file_path):
    layout_values = calculate_layout_efficiency.schematic_to_values(file_path)
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
    # function to prompt the user to select a file
    file_path = filedialog.askopenfilename()
    if file_path:
        output(file_path)
        return file_path


button = tk.Button(root, text="Select Schematic", bg=colours.warped, font=main_font,
                   command=lambda: path.set(select_file()))
button.grid(row=0, column=1, pady=15)

path = tk.StringVar()

labels = {}
# define block types
output_labels = [
    "    Stems    ",
    " Shroomlights",
    " Wart Blocks "
]

for i, output_label in enumerate(output_labels):
    label = tk.Label(root, text=output_label, bg=colours.dark_orange, fg=colours.fg, font=main_font)
    label.grid(row=1, column=i)
    labels[i] = label  # add the label to the dictionary with key 'i'

    value_label = tk.Label(root, text="", bg=colours.bg, fg=colours.fg, font=output_font)
    value_label.grid(row=2, column=i)
    labels[i + 3] = value_label  # add the output label to the dictionary with key 'i+3'
    value_label = tk.Label(root, text="", bg=colours.bg, fg=colours.fg, font=output_font)
    value_label.grid(row=3, column=i)
    labels[i + 6] = value_label  # add the output label to the dictionary with key 'i+3'

schematic_display = tk.Frame(root)
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
vrms_frame = tk.Frame(root)
vrms_frame.grid(row=6, column=0, columnspan=3)
vrms_frame.configure(bg=colours.bg)

for j, val2 in enumerate(vrms_labels):
    label2 = tk.Label(vrms_frame, text=val2, width=10, bg=colours.dark_blue_grey, fg=colours.fg, font=main_font)
    label2.grid(row=0, column=j)
    vrm_labels[j] = label2

    label2 = tk.Label(vrms_frame, text="", bg=colours.bg, fg=colours.fg, font=output_font)
    label2.grid(row=1, column=j)
    vrm_labels[j + 4] = label2

root.mainloop()
