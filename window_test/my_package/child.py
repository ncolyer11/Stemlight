from PIL import Image, ImageTk
import tkinter as tk
import pkg_resources

import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def run_python_code():
    image_path = resource_path('my_package/images/test.png')

    # Create a Tkinter window
    window = tk.Toplevel()

    # Open the image file with PIL and create a PhotoImage
    image = Image.open(image_path)

    # Rotate the image 90 degrees to the right
    image = image.rotate(90, expand=True)

    # Resize the image
    base_width = 1000
    width_percent = (base_width / float(image.size[0]))
    hsize = int((float(image.size[1]) * float(width_percent)))
    image = image.resize((base_width, hsize), Image.ANTIALIAS)

    photo = ImageTk.PhotoImage(image)

    # Create a label with the image and pack it into the window
    label = tk.Label(window, image=photo)
    label.image = photo  # Keep a reference to the image
    label.pack()

    # Start the Tkinter event loop
    window.mainloop()