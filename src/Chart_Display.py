import ctypes
import math
import tkinter as tk
import tkinter.font as font
from PIL import Image, ImageTk
import os

from src.Assets import colours
from src.Assets.constants import RSF
from src.Assets.version import version
from src.Assets.helpers import resource_path, set_title_and_icon

MAX_COL = 9

def start(root):
    def open_image(image_file_path, photo):
        image2 = Image.open(image_file_path)
        screen_width = child.winfo_screenwidth()
        screen_height = child.winfo_screenheight()
        max_width = screen_width - 100
        max_height = screen_height - 100
        resized_image = image2.copy()
        resized_image.thumbnail((max_width, max_height))
        new_window = tk.Toplevel(child)
        set_title_and_icon(new_window, os.path.basename(image_file_path))
        new_window.resizable(0, 0)
        img = ImageTk.PhotoImage(resized_image)
        label = tk.Label(new_window, image=img)
        label.image = img
        label.pack()

    child = tk.Toplevel(root)
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
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    image_files = {
        "7 different regions.png": "\nDifferent Regions",
        "Shroomlight Heatmap v2 3D.jpg": "\nShroomlight Heatmap",
        "shrooms per layer v2.jpg": "\nShroomlights per Layer",
        "vrm optimal placements heatmap.png": "\nWart Blocks per VRM",
        "Shroomlight Distribution.png": "\nShroomlight Distribution",
        "Wart Block Heatmap v2 3D.jpg": "\nWart Block Heatmap",
        "warts per layer v2.jpg": "\nWart Blocks per Layer",
        "vrm raw placements heatmap.png": "\nRaw Wart Blocks per VRM",
        "internal_region_heatmap.png": "\nInternal Region Heatmap\n(Warts)",
        "external_region_heatmap.png": "\nExternal Region Heatmap\n(Shrooms)",
        "corners_region_heatmap.png": "\nCorners Region Heatmap\n(Shrooms)",
        "vines_region_heatmap.png": "\nVines Region Heatmap\n(Warts)",
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

    S = 1.3
    thumbnail_width = round(320 * S)
    thumbnail_height = round(240 * S)

    photo_images = []
    button_widgets = []
    caption_widgets = []

    def calculate_columns():
        screen_width = child.winfo_width()
        available_width = screen_width - 40
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

    def center_frame(event):
        canvas_width = canvas.winfo_width()
        frame_width = scrollable_frame.winfo_reqwidth()
        canvas.coords("frame", canvas_width // 2 - frame_width // 2, 0)
        update_grid()

    canvas.bind("<Configure>", center_frame)
    child.bind("<Configure>", lambda event: update_grid())

    for path, caption_text in zip(image_paths, image_files.values()):
        image = Image.open(path)
        image.thumbnail((thumbnail_width, thumbnail_height))
        new_image = Image.new("RGB", (thumbnail_width, thumbnail_height), colours.bg)
        paste_x = (thumbnail_width - image.width) // 2
        paste_y = (thumbnail_height - image.height) // 2
        new_image.paste(image, (paste_x, paste_y))

        photo = ImageTk.PhotoImage(new_image)
        photo_images.append(photo)

        button = tk.Button(scrollable_frame, image=photo, command=lambda path=path, photo=photo: open_image(path, photo))
        button_widgets.append(button)

        caption = tk.Label(scrollable_frame, text=caption_text, bg=colours.bg, fg=colours.fg, font=main_font)
        caption_widgets.append(caption)

    update_grid()

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    child.mainloop()
