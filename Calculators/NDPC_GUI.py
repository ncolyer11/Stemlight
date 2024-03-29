import tkinter as tk
from tkinter import ttk


class CheckButtonGrid:
    var_dict = {}

    def __init__(self, master, length, width):
        self.master = master
        self.length = length
        self.width = width
        self.create_grid()

    def create_grid(self):
        for i in range(self.length):
            for j in range(self.width):
                var = tk.IntVar(value=0)  # set initial value to 0
                self.var_dict[(i, j)] = var
                cb = ttk.Checkbutton(self.master, variable=var, offvalue=0)  # set offvalue to 0
                cb.grid(row=i, column=j + 2)

    def get_states(self):
        return [[self.var_dict[(i, j)].get() for j in range(self.width)] for i in range(self.length)]


class App:
    def __init__(self, master):
        self.master = master
        self.length_entry = tk.Entry(self.master)
        self.width_entry = tk.Entry(self.master)
        self.number_entry = tk.Entry(self.master)
        self.create_widgets()

    def create_widgets(self):
        # create input widgets
        tk.Label(self.master, text="Length:").grid(row=0, column=0)
        self.length_entry.grid(row=0, column=1)

        tk.Label(self.master, text="Width:").grid(row=1, column=0)
        self.width_entry.grid(row=1, column=1)

        tk.Label(self.master, text="Number:").grid(row=2, column=0)
        self.number_entry.grid(row=2, column=1)

        # create submit button
        tk.Button(self.master, text="Create Grid", command=self.create_grid).grid(row=3, column=0, columnspan=2)

    def create_grid(self):
        # get input values
        length = int(self.length_entry.get())
        width = int(self.width_entry.get())
        number = int(self.number_entry.get())

        # create check button grid
        cbg = CheckButtonGrid(self.master, length, width)

        # set initial values of check buttons based on input number
        for i in range(length):
            for j in range(width):
                if (i * width + j) < number:
                    cbg.var_dict[(i, j)].set(1)

        # create button to get check button states
        tk.Button(self.master, text="Get States", command=lambda: self.get_states(cbg)).grid(row=4, column=0,
                                                                                             columnspan=2)

    def get_states(self, cbg):
        states = cbg.get_states()
        print(states)


root = tk.Tk()
app = App(root)
root.mainloop()
