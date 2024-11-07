"""Displays charts on various nether tree farm\nrelated statistics and phenomena"""

import os
import math
import tkinter as tk
import tkinter.font as font
from PIL import Image, ImageTk
import ctypes

from Main_Menu import ToolTip
from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.helpers import resource_path, set_title_and_icon, program_window_counter, \
    all_program_instances

MAX_COL = 9

def start(root):
    def center_frame(event):
        canvas_width = canvas.winfo_width()
        frame_width = scrollable_frame.winfo_reqwidth()
        canvas.coords("frame", canvas_width // 2 - frame_width // 2, 0)
        update_grid()
        
    def calculate_columns():
        screen_width = child.winfo_width()
        available_width = screen_width - 250
        max_thumbnail_width = 370 * S
        cols = max(1, available_width // max_thumbnail_width)
        return min(MAX_COL, math.floor(cols))

    def update_grid():
        cols = calculate_columns()
        for i, (button, caption) in enumerate(zip(button_widgets, caption_widgets)):
            row = 2 * (i // cols)
            col = i % cols
            button.grid(row=row + 1, column=col, padx=10, pady=10)
            caption.grid(row=row, column=col, padx=10, pady=3)

    def open_image(image_file_path, photo):
        # Get the actual screen's width and height
        image2 = Image.open(image_file_path)
        screen_width = child.winfo_screenwidth()
        screen_height = child.winfo_screenheight()
        try: 
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
        except:
            pass
        max_width = screen_width - 50
        max_height = screen_height - 50
        
        # Get original image size
        original_width, original_height = image2.size
        
        # Calculate resize ratio while maintaining aspect ratio
        ratio = min(max_width / original_width, max_height / original_height, 1)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        resized_image = image2.resize((new_width, new_height))
        
        new_window = tk.Toplevel(child)
        set_title_and_icon(new_window, os.path.basename(image_file_path))
        
        img = ImageTk.PhotoImage(resized_image)
        label = tk.Label(new_window, image=img)
        label.image = img
        label.pack()
        
        # Set the window size to the resized image size
        new_window.geometry(f"{new_width}x{new_height}+25+25")
        new_window.resizable(0, 0)
    
    child = tk.Toplevel(root)
    all_program_instances[program_window_counter] = child  # Track the instance
    set_title_and_icon(child, "Chart Viewer")
    child.configure(bg=colours.bg)
    child.state('zoomed')

    main_font = font.Font(family='Segoe UI Semibold', size=int((RSF**1.765)*12))

    toolbar = tk.Menu(child)
    child.config(menu=toolbar)
    file_menu = tk.Menu(toolbar, tearoff=0, font=("Segoe UI", int((RSF**0.7)*12)))
    toolbar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=child.destroy)

    canvas = tk.Canvas(child, bg=colours.bg)
    scrollbar = tk.Scrollbar(child, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=colours.bg)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="frame")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mouse_wheel(event):
        # Check if the current window has focus
        # Using the walrus operator to assign and check the value of the current focused instance
        if child == event.widget.winfo_toplevel(): # instance here is our canvas
            # Check if the focused widget is the canvas
            # Get the current scroll position
            current_scroll_position = canvas.yview()

            # Limit values, e.g., preventing the upper scroll to be less than 0.1 (10% down from top)
            min_scroll = 0   # Set your desired upper limit
            max_scroll = 1.0   # Maximum scroll value corresponds to the bottom-most position

            # Calculate the new scroll position based on mouse wheel delta
            new_scroll_position = current_scroll_position[0] + (-1 * (event.delta / 120) / 10)

            # Check and enforce the scroll limits
            if new_scroll_position < min_scroll:
                canvas.yview_moveto(min_scroll)
            elif new_scroll_position > max_scroll:
                canvas.yview_moveto(max_scroll)
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    child.bind("<MouseWheel>", _on_mouse_wheel)

    image_files = {
        "7 different regions.png": {
            "caption": "\nDifferent Regions",
            "tooltip": "Note that the 3rd (light blue), vines layer\nfor the far left tree should be VL1 (dark blue)"
        },
        "Shroomlight Heatmap v2 3D.jpg": {
            "caption": "\nShroomlight Heatmap",
            "tooltip": ""
        },
        "Wart Block Heatmap v2 3D.jpg": {
            "caption": "\nWart Block Heatmap",
            "tooltip": ""
        },
        "Shroomlight Distribution.png": {
            "caption": "\nShroomlight Distribution",
            "tooltip": ""
        },
        "fungus_growth_chance.png": {
            "caption": "\nFungus Growth Chance",
            "tooltip": ""
        },
        "trunk_height_probability_distribution.png": {
            "caption": "\nTrunk Height Chances",
            "tooltip": "Chance of a certain trunk height being picked after a fungus grows"
        },
        "shrooms per layer v2.jpg": {
            "caption": "\nShroomlights per Layer",
            "tooltip": ""
        },
        "warts per layer v2.jpg": {
            "caption": "\nWart Blocks per Layer",
            "tooltip": ""
        },
        "trunk_layers_vs_efficiency.png": {
            "caption": "\nTrunk Efficiency",
            "tooltip": "Percentage of stems harvested per fungi\nas you harvest more layers "
        },
        "hat_height_probability_distribution.png": {
            "caption": "\nHat Height Chances",
            "tooltip": "Note the hat height seen in-game is 1 block higher\nthan what's shown in the graph"
        },
        "trunk_and_hat_height_pair_probabilities.png": {
            "caption": "\nTrunk-Hat Pair Height Chances",
            "tooltip": "Chance of growing a fungus with a certain trunk and hat height.\nMultiply the hat height chance by the trunk height\nchance on the right to get the total probability"
        },
        "internal_region_heatmap.png": {
            "caption": "\nInternal Region Heatmap\n(Warts)",
            "tooltip": "Chance of a wart block generating in just the internal region"
        },
        "external_region_heatmap.png": {
            "caption": "\nExternal Region Heatmap\n(Shrooms)",
            "tooltip": "Chance of a shromlight generating in just the external region"
        },
        "corners_region_heatmap.png": {
            "caption": "\nCorners Region Heatmap\n(Shrooms)",
            "tooltip": "Chance of a shroomlight generating in just the corners region"
        },
        "vines_region_heatmap.png": {
            "caption": "\nVines Region Heatmap\n(Warts)",
            "tooltip": "Chance of a wart block generating in just the vines region (no VRM)"
        },
        "vrm optimal placements heatmap.png": {
            "caption": "\nWart Blocks per VRM",
            "tooltip": "Additional wart blocks generated per cycle for a\npre-placed VRM wart block placed at that given position"
        },
        "vrm raw placements heatmap.png": {
            "caption": "\nRaw Wart Blocks per VRM",
            "tooltip": "Additional wart blocks generated from VRM,\nnot taking into account the wart blocks lost\nvia blocking from the pre-placed wart block"
        },
        "warped_fungus_distribution_5x5_dispenser.png": {
            "caption": "\nWarped Fungi Spread (%)",
            "tooltip": "Fungus distribution after bone-mealing a 5x5 platform of warped nyliium"
        },
        "crimson_fungus_distribution_5x5_dispenser.png": {
            "caption": "\nCrimson Fungi Spread (%)",
            "tooltip": "Fungus distribution after bone-mealing a 5x5 platform of crimson nyliium"
        },
        "warped_vs_crimson_distribution_repeated_bone_meals.png": {
            "caption": "\nFungi after X Bone Meals",
            "tooltip": "Total fungi generated after bone-mealing a 5x5 platform\nof warped vs crimson nylium a repeated amount of times"
        }
    }

    image_paths = [resource_path(f"src/Images/{image}") for image in image_files.keys()]

    S = 1.3
    thumbnail_width = round(320 * S)
    thumbnail_height = round(240 * S)

    photo_images = []
    button_widgets = []
    caption_widgets = []

    canvas.bind("<Configure>", center_frame)
    child.bind("<Configure>", lambda event: update_grid())
    tooltips = []
    
    # Load the placeholder image or create an empty one if it doesn't exist
    invisible_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))  # Transparent 1x1 image
    invisible_photo = ImageTk.PhotoImage(invisible_image)  # Make it a PhotoImage for Tkinter

    for path, details in zip(image_paths, image_files.values()):
        if path.endswith("invisible_placeholder.png"):
            photo = invisible_photo
        else:
            image = Image.open(path)
            image.thumbnail((thumbnail_width, thumbnail_height))
            new_image = Image.new("RGB", (thumbnail_width, thumbnail_height), colours.bg)
            paste_x = (thumbnail_width - image.width) // 2
            paste_y = (thumbnail_height - image.height) // 2
            new_image.paste(image, (paste_x, paste_y))

            photo = ImageTk.PhotoImage(new_image)
            photo_images.append(photo)

        # Create the button and capture `details` correctly in a lambda
        button = tk.Button(scrollable_frame, image=photo, command=lambda path=path: open_image(path, photo))
        button_widgets.append(button)

        caption = tk.Label(scrollable_frame, text=details["caption"], bg=colours.bg, fg=colours.fg, font=main_font)
        caption_widgets.append(caption)

        # Create tooltip instance for the button
        tooltip = ToolTip(button, details["tooltip"])
        tooltips.append(tooltip)

    update_grid()
    
    child.mainloop()




