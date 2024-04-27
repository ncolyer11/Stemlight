import tkinter as tk
from tkinter import ttk
import time

class App:
    def __init__(self, master):
        self.master = master
        self.grid = []
        self.dispensers = []
        self.create_widgets()

    def create_widgets(self):
        self.row_slider = tk.Scale(self.master, from_=1, to=100, orient=tk.HORIZONTAL, command=self.update_grid)
        self.row_slider.pack()
        self.col_slider = tk.Scale(self.master, from_=1, to=100, orient=tk.HORIZONTAL, command=self.update_grid)
        self.col_slider.pack()
        self.grid_frame = tk.Frame(self.master)
        self.grid_frame.pack()
        self.calc_button = tk.Button(self.master, text="Calculate", command=self.calculate)
        self.calc_button.pack()

    def update_grid(self, _):
        for row in self.grid:
            for cb in row:
                cb.destroy()
        self.grid = []
        self.dispensers = []
        rows = self.row_slider.get()
        cols = self.col_slider.get()
        for i in range(rows):
            row = []
            for j in range(cols):
                var = tk.IntVar()
                cb = ttk.Checkbutton(self.grid_frame, variable=var, command=lambda x=i, y=j: self.add_dispenser(x, y))
                cb.grid(row=i, column=j)
                row.append(cb)
            self.grid.append(row)

    def add_dispenser(self, x, y):
        self.dispensers.append((x, y, time.time()))

    def calculate(self):
        self.dispensers.sort(key=lambda d: d[2])
        # Start the calculation here

root = tk.Tk()
app = App(root)
root.mainloop()