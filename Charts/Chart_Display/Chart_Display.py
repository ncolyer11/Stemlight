import tkinter as tk
import tkinter.font as font
from PIL import Image, ImageTk
from Assets import colours


# Function to open the selected image in a new window
def open_image(image_file_path):
    image2 = Image.open(image_file_path)

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the maximum allowable width and height
    max_width = screen_width - 100  # Adjusted for padding
    max_height = screen_height - 100  # Adjusted for padding

    # Resize image to fit within the screen dimensions
    resized_image = image2.copy()
    resized_image.thumbnail((max_width, max_height))

    # Create a new window
    new_window = tk.Toplevel(root)
    new_window.title(image_file_path[7:])
    new_window.iconbitmap('./Assets/ikon.ico')
    img = ImageTk.PhotoImage(resized_image)
    label = tk.Label(new_window, image=img)
    label.image = img  # Keep a reference to the image object
    label.pack()


# Create the main Tkinter window
root = tk.Tk()
root.title("Stemlight: Chart Viewer")
root.iconbitmap('./Assets/ikon.ico')
root.configure(bg=colours.bg)
root.geometry("+0+0")
root.minsize(1400, 700)


main_font = font.Font(family='Segoe UI Semibold', size=14)

toolbar = tk.Menu(root)
root.config(menu=toolbar)
file_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)


# Define the image folder path
image_folder = "Charts/"

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

# Create a 2x3 button grid
MAX_ROW = 2
MAX_COL = 4

for i, image_file in enumerate(image_files):
    row = MAX_ROW * (i // MAX_COL)
    col = i % MAX_COL
    image_path = image_folder + image_file
    image = Image.open(image_path)

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

    button = tk.Button(root, image=photo, command=lambda path=image_path: open_image(path))
    button.grid(row=row + 1, column=col, padx=10, pady=10)

    # Save reference to the photo object to prevent it from being garbage collected
    button.photo = photo

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

    caption = tk.Label(root, text=captions[i], bg=colours.bg, fg=colours.fg, font=main_font)
    caption.grid(row=row, column=col, padx=10, pady=3)

# Run the Tkinter event loop
root.mainloop()
