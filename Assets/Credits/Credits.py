import tkinter as tk
from tkinter import ttk

from Assets import colours

credits_text = (
    "Made by: ncolyer\n"
    "Created: 2023\n"
    "Version: 0.3.1-alpha"
)

# Create the main window
root = tk.Tk()
root.title("Stemlight: Credits")

# Set the window icon
icon_path = "./Assets/ikon.ico"
root.iconbitmap(icon_path)

# Set the window size
window_width = 275
window_height = 250
root.geometry(f"{window_width}x{window_height}")
root.configure(bg=colours.bg)

# Style for the text
style = ttk.Style(root)
style.configure("TLabel", font=("Segoe UI Semibold", 14), padding=(5, 5), background=colours.dark_orange)
style.configure("Title.TLabel", font=("Segoe UI Semibold", 20), padding=(5, 5))

# Create and place a title label
title_label = ttk.Label(root, text="Stemlight", justify="center", style="Title.TLabel")
title_label.grid(row=0, column=0, padx=10, pady=10)

# Create and place a label for the credits text
label = ttk.Label(root, text=credits_text, justify="center", style="TLabel", background=colours.menu_gradient[1])
label.grid(row=1, column=0, padx=10, pady=10)

# Center the content in the window
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Run the main loop for the window
root.mainloop()
