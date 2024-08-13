import sys
import tkinter
from PIL import Image, ImageTk

# Create the main window
path = "openmoji-618x618-color/1F600.png"
root = tkinter.Tk()
root.title("Tkinter Canvas Image Example")

# Create a canvas widget
canvas = tkinter.Canvas(root, width=400, height=400)
canvas.pack()

# Load an image file using PIL
image = Image.open(path)
resized_image = image.resize((16, 16))
tk_image = ImageTk.PhotoImage(resized_image)
        
canvas.create_image(100,100, image=tk_image)

# Start the Tkinter event loop
root.mainloop()
