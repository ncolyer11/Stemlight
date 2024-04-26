import tkinter as tk
from my_package import child

def run_python_code():
    # Call a function from the imported module
    child.run_python_code()

def open_child_window():
    child_window = tk.Toplevel(root)
    child_window.title("Child Window")

    # Add a button to run the Python code in the child window
    run_button = tk.Button(child_window, text="Run Python Code", command=run_python_code)
    run_button.pack()

# Create the main window
root = tk.Tk()
root.title("Main Window")

# Add a button to open the child window
open_button = tk.Button(root, text="Open Child Window", command=open_child_window)
open_button.pack()

# Start the main event loop
root.mainloop()

# to create the executable run this command:
# pyinstaller --onefile --windowed --add-data "my_package/images/*;my_package/images" main_menu.py