"""Displays various nether tree farming-related charts at a glance"""

import tkinter as tk
import tkinter.font as font
from PIL import Image, ImageTk
import os

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version
from src.Assets.helpers import resource_path, set_title_and_icon

MAX_COL = 4

def start(root):
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
        set_title_and_icon(new_window, os.path.basename(image_file_path))
        new_window.resizable(0, 0)

        img = ImageTk.PhotoImage(resized_image)
        label = tk.Label(new_window, image=img)
        label.image = img  # Keep a reference to the image object
        label.pack()

    # Create the child Tkinter window
    child = tk.Toplevel(root)
    set_title_and_icon(child, "Chart Viewer")
    child.configure(bg=colours.bg)
    child.state('zoomed') # Works for Windows and Linux

    main_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*12))

    toolbar = tk.Menu(child)
    child.config(menu=toolbar)
    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.destroy)

    # Create a Canvas and Scrollbar for scrolling
    canvas = tk.Canvas(child, bg=colours.bg)
    scrollbar = tk.Scrollbar(child, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=colours.bg)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mouse_wheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Bind mouse wheel events to the canvas
    canvas.bind_all("<MouseWheel>", _on_mouse_wheel)  # Windows and macOS
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Some Linux systems
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Some Linux systems

    # List of image file names
    image_files = {
        "7 different regions.png": "\nDifferent Regions",
        "Shroomlight Heatmap v2 3D.jpg": "\nShroomlight Heatmap",
        "shrooms per layer v2.jpg": "\nShroomlights per Layer",
        "vrm optimal placements heatmap.png": "\nWart Blocks per VRM",
        "Shroomlight Distribution.png": "\nShroomlight Distribution",
        "Wart Block Heatmap v2 3D.jpg": "\nWart Block Heatmap",
        "warts per layer v2.jpg": "\nWart Blocks per Layer",
        "vrm raw placements heatmap.png": "\nRaw Wart Blocks per VRM",
        "internal_region_heatmap.png": "\nInternal Region Heatmap (Warts)",
        "external_region_heatmap.png": "\nExternal Region Heatmap (Shrooms)",
        "corners_region_heatmap.png": "\nCorners Region Heatmap (Shrooms)",
        "vines_region_heatmap.png": "\nVines Region Heatmap (Warts)",
        "trunk_height_probability_distribution.png": "\nTrunk Height Chances",
        "trunk_layers_vs_efficiency.png": "\nTrunk Efficiency",
        "fungus_growth_chance.png": "\nFungus Growth Chance",
        "hat_height_probability_distribution.png": "\nHat Height Chances",
        "trunk_and_hat_height_pair_probabilities.png": "\nTrunk-Hat Pair Height Chances",
        "crimson_fungus_distribution_5x5_dispenser.png": "\nCrimson Fungi Spread (%)",
        "warped_fungus_distribution_5x5_dispenser.png": "\nWarped Fungi Spread (%)",
        "warped_vs_crimson_distribution_repeated_bone_meals.png": "\nFungi after X Bone Meals"
    }

    image_paths = [resource_path(f"src/Images/{image}") for image in image_files.keys()]

    # Calculate the desired thumbnail width and height
    S = 1.3
    thumbnail_width = round(320 * S)
    thumbnail_height = round(180 * S)

    # Set the maximum thumbnail size
    max_thumbnail_width = round(370 * S)
    max_thumbnail_height = round(300 * S)

    # Calculate the aspect ratio of the thumbnails
    aspect_ratio = thumbnail_width / thumbnail_height

    # Create a list to store the PhotoImage objects
    photo_images = []

    # Create the thumbnail button grid
    for i, (path, caption_text) in enumerate(zip(image_paths, image_files.values())):
        row = 2 * (i // MAX_COL)
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

        button = tk.Button(scrollable_frame, image=photo, command=lambda path=path,
                           photo=photo: open_image(path, photo))
        button.grid(row=row + 1, column=col, padx=10, pady=10)

        # Save reference to the photo object to prevent it from being garbage collected
        button.image = photo

        # Add captions below each image
        caption = tk.Label(scrollable_frame, text=caption_text, bg=colours.bg, fg=colours.fg, font=main_font)
        caption.grid(row=row, column=col, padx=10, pady=3)

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    child.mainloop()
