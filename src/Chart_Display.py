import tkinter as tk
import tkinter.font as font
from PIL import Image, ImageTk
import os
import sys

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version

def start(root):
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # Function to open the selected image in a new window
    def open_image(image_file_path, photo):
        image2 = Image.open(image_file_path)

        # Get screen dimensions
        screen_width = child.winfo_screenwidth()
        screen_height = child.winfo_screenheight()

        # Calculate the maximum allowable width and height
        max_width = screen_width - 100  # Adjusted for padding
        max_height = screen_height - 100  # Adjusted for padding

        # Resize image to fit within the screen dimensions
        resized_image = image2.copy()
        resized_image.thumbnail((max_width, max_height))

        # Create a new window
        new_window = tk.Toplevel(child)
        new_window.title(os.path.basename(image_file_path))
        try:
            # Try to use the .ico file
            icon_path = resource_path('src/Assets/icon.ico')
            root.iconbitmap(icon_path)
        except:
            # If that fails, try to use the .xbm file
            try:
                icon_path = resource_path('src/Assets/icon.xbm')
                root.iconbitmap('@' + icon_path)
            except:
                pass  # If that also fails, do nothing
        new_window.resizable(0,0)

        img = ImageTk.PhotoImage(resized_image)
        label = tk.Label(new_window, image=img)
        label.image = img  # Keep a reference to the image object
        label.pack()

    # Create the child Tkinter window
    child = tk.Toplevel(root)
    child.title(f"Stemlight{version}: Chart Viewer")
    try:
        # Try to use the .ico file
        icon_path = resource_path('src/Assets/icon.ico')
        root.iconbitmap(icon_path)
    except:
        # If that fails, try to use the .xbm file
        try:
            icon_path = resource_path('src/Assets/icon.xbm')
            root.iconbitmap('@' + icon_path)
        except:
            pass  # If that also fails, do nothing
    child.resizable(0,0)
    child.configure(bg=colours.bg)
    child.geometry("+0+0")
    child.minsize(1400, 700)


    main_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*12))

    toolbar = tk.Menu(child)
    child.config(menu=toolbar)
    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.quit)

    # List of image file names
    image_files = [
        "7 different regions.png",
        "Shroomlight Heatmap v2 3D.jpg",
        "shrooms per layer v2.jpg",
        "vrm optimal placements heatmap.png",
        "Shroomlight Distribution.png",
        "Wart Block Heatmap v2 3D.jpg",
        "warts per layer v2.jpg",
        "vrm raw placements heatmap.png"
    ]

    image_paths = [resource_path(f"src/images/{image}") for image in image_files]

    # Calculate the desired thumbnail width and height
    thumbnail_width = 320
    thumbnail_height = 180

    # Set the maximum thumbnail size
    max_thumbnail_width = 370
    max_thumbnail_height = 300

    # Calculate the aspect ratio of the thumbnails
    aspect_ratio = thumbnail_width / thumbnail_height

    # Create a list to store the PhotoImage objects
    photo_images = []

    # Create a 2x4 button grid
    MAX_ROW = 2
    MAX_COL = 4

    for i, path in enumerate(image_paths):
        row = MAX_ROW * (i // MAX_COL)
        col = i % MAX_COL
        image = Image.open(path)

        # Calculate the thumbnail size while preserving the aspect ratio
        image_width, image_height = image.size
        image_aspect_ratio = image_width / image_height

        if image_aspect_ratio > aspect_ratio:
            # Image is wider, adjust the width and calculate the proportional height
            thumbnail_width = min(max_thumbnail_width, image_width)
            thumbnail_height = int(thumbnail_width / image_aspect_ratio)
            thumbnail_size = (thumbnail_width, thumbnail_height)
        else:
            # Image is taller or has the same aspect ratio, adjust the height and calculate the proportional width
            thumbnail_height = min(max_thumbnail_height, image_height)
            thumbnail_width = int(thumbnail_height * image_aspect_ratio)
            thumbnail_size = (thumbnail_width, thumbnail_height)

        thumbnail = image.resize(thumbnail_size)
        bordered_thumbnail = Image.new("RGB", (thumbnail_width + 2, thumbnail_height + 2))
        bordered_thumbnail.paste(thumbnail, (1, 1))
        photo = ImageTk.PhotoImage(bordered_thumbnail)
        photo_images.append(photo)  # Store the PhotoImage object in the list

        button = tk.Button(child, image=photo, command=lambda path=path,
                           photo=photo: open_image(path, photo))
        button.grid(row=row + 1, column=col, padx=10, pady=10)

        # Save reference to the photo object to prevent it from being garbage collected
        button.image = photo

        # Add captions below each image
        captions = [
            "\nDifferent Regions",
            "\nShroomlight Heatmap",
            "\nShroomlights per Layer",
            "\nWart Blocks per VRM",
            "\nShroomlight Distribution",
            "\nWart Block Heatmap",
            "\nWart Blocks per Layer",
            "\nRaw Wart Blocks per VRM"
        ]

        caption = tk.Label(child, text=captions[i], bg=colours.bg, fg=colours.fg, font=main_font)
        caption.grid(row=row, column=col, padx=10, pady=3)

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    child.mainloop()
