import os
import sys
import tkinter as tk
from tkinter import ttk
import tkinter.font as font
import time
import Assets.colours as colours
from Assets.constants import RSF
from Assets.helpers import set_title_and_icon

# Non-linear scaling factor
NLS = 1.765

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class App:
    def __init__(self, master):
        self.master = master
        self.grid = []
        self.dispensers = []
        self.vars = []
        self.create_widgets()

    def create_widgets(self):
        self.master.configure(bg=colours.bg)
        style = ttk.Style()
    
        # Define the font
        button_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*11))
        checkbox_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*15))
        slider_font = font.Font(family='Segoe UI Semibold', size=int((RSF**NLS)*15))
    
        style.configure(
            "TCheckbutton", 
            indicatorsize=120, 
            foreground=colours.bg, 
            background=colours.warped, 
            font=checkbox_font
        )
        style.configure("TScale", font=slider_font)

        # Create images for the checked and unchecked states
        checked_path = resource_path('src/Assets/icon.ico')
        self.checked_image = tk.PhotoImage(file=checked_path)
        self.unchecked_image = tk.PhotoImage(file="src/Images/warped_nylium.png")

        # Resize the images
        self.checked_image = self.checked_image.subsample(4, 4)
        self.unchecked_image = self.unchecked_image.subsample(4, 4)
    
        self.row_slider = tk.Scale(
            self.master, 
            from_=1, 
            to=10, 
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.row_slider.set(5)
        self.row_slider.pack(pady=10)
        self.row_slider.pack()

        self.col_slider = tk.Scale(
            self.master, 
            from_=1, 
            to=10, 
            orient=tk.HORIZONTAL, 
            command=self.update_grid, 
            bg=colours.bg, 
            fg=colours.fg, 
            length=250
        )
        self.col_slider.set(5)
        self.col_slider.pack(pady=1)
        self.col_slider.pack()

        self.grid_frame = tk.Frame(self.master, bg=colours.bg, padx=10, pady=10)
        self.grid_frame.pack()
        self.calc_button = tk.Button(self.master, text="Calculate", command=self.calculate, font=button_font, bg=colours.crimson)
        self.calc_button.pack()


    def update_grid(self, _):
        # Save the states of the checkboxes
        saved_states = [[var.get() for var in var_row] for var_row in self.vars]
    
        for row in self.grid:
            for cb in row:
                cb.destroy()
        self.grid = []
        self.dispensers = []
        self.vars = []
        rows = self.row_slider.get()
        cols = self.col_slider.get()
        for i in range(rows):
            row = []
            var_row = []
            for j in range(cols):
                var = tk.IntVar()
                cb = tk.Button(
                    self.grid_frame,
                    image=self.unchecked_image,
                    borderwidth=0,
                    highlightthickness=0,
                    bd=1,
                    bg=colours.phtalo_green,
                    command=lambda x=i, y=j: self.add_dispenser(x, y)
                )
                cb.grid(row=i, column=j, padx=0, pady=0)
                row.append(cb)
                var_row.append(var)
                # Restore the state of the checkbox, if it existed before
                if i < len(saved_states) and j < len(saved_states[i]):
                    var.set(saved_states[i][j])
                    if saved_states[i][j] == 1:
                        cb.config(image=self.checked_image)
                        self.dispensers.append((i, j, time.time()))
            self.grid.append(row)
            self.vars.append(var_row)

    def add_dispenser(self, x, y):
        # Toggle the state of the checkbox
        self.vars[x][y].set(not self.vars[x][y].get())

        # Update the image based on the state of the checkbox
        if self.vars[x][y].get() == 0:
            self.grid[x][y].config(image=self.unchecked_image)
            self.dispensers = [d for d in self.dispensers if d[:2] != (x, y)]
        else:
            self.grid[x][y].config(image=self.checked_image)
            self.dispensers.append((x, y, time.time()))

    def calculate(self):
        self.dispensers.sort(key=lambda d: d[2])
        for dispenser in self.dispensers:
            print(dispenser[:3])
        print()

def start():
    root = tk.Tk()
    set_title_and_icon(root, "Dispenser Placement")

    root.configure(bg=colours.bg)
    root.minsize(int(RSF*300), int(RSF*305))

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = App(root)
    root.mainloop()
start()
