import tkinter as tk

root = tk.Tk()

# Create images for the checked and unchecked states
checked_image = tk.PhotoImage(file="src/Images/dispenser.png")  # Replace with your own image
unchecked_image = tk.PhotoImage(file="src/Images/warped_nylium.png")  # Replace with your own image

# Resize the images
checked_image = checked_image.subsample(2, 2)  # Increase the numbers to make the image smaller
unchecked_image = unchecked_image.subsample(2, 2)  # Increase the numbers to make the image smaller

# Create a variable to hold the state of the checkbox
check_var = tk.IntVar()

def toggle_check():
    # Toggle the state of the checkbox
    check_var.set(not check_var.get())

    # Update the image based on the state of the checkbox
    if check_var.get() == 0:
        check_button.config(image=unchecked_image)
    else:
        check_button.config(image=checked_image)

# Create a button that acts like a checkbox
check_button = tk.Button(root, image=unchecked_image, command=toggle_check)
check_button.pack()

# Create a checkbutton that controls the state of the custom checkbox
# We make this invisible by not packing it
check = tk.Checkbutton(root, variable=check_var, command=toggle_check)

root.mainloop()