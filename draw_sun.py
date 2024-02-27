from PIL import Image
from PIL import ImageDraw
import time
import math
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
# or 'adafruit-hat' if you're using Adafruit's HAT/Pi Bonnet
options.hardware_mapping = 'adafruit-hat'

matrix = RGBMatrix(options=options)

# Coordinates where you want to place the sun within the larger matrix
sun_position_x = 24  # change to position the sun
sun_position_y = 8  # change to position the sun

# Create a new image to draw the sun icon (smaller than the main matrix)
icon_size = 16  # dimensions for the sun icon
sun_image = Image.new("RGB", (icon_size, icon_size))
draw_icon = ImageDraw.Draw(sun_image)

# Draw a yellow circle (filled) for the sun's body
sun_center = (icon_size // 2, icon_size // 2)
sun_radius = 5  # appropriate for the 16x16 icon
sun_color = (255, 255, 0)  # yellow

draw_icon.ellipse(
    [
        sun_center[0] - sun_radius,
        sun_center[1] - sun_radius,
        sun_center[0] + sun_radius,
        sun_center[1] + sun_radius
    ],
    fill=sun_color
)

# Draw lines for the sun's rays
num_rays = 8
ray_length = 3  # appropriate for the 16x16 icon
ray_color = (255, 255, 0)  # yellow

for i in range(num_rays):
    angle = 360 / num_rays * i
    x_end = sun_center[0] + (sun_radius + ray_length) * \
        math.cos(math.radians(angle))
    y_end = sun_center[1] + (sun_radius + ray_length) * \
        math.sin(math.radians(angle))

    draw_icon.line((sun_center[0], sun_center[1],
                   x_end, y_end), fill=ray_color)

# Now, we'll position the smaller sun icon image within the larger matrix.
# We create a new image with the dimensions of the matrix and paste the sun icon onto it.
matrix_image = Image.new("RGB", (options.cols, options.rows))
# Position the sun icon
matrix_image.paste(sun_image, (sun_position_x, sun_position_y))

# Display the final image on the LED matrix
matrix.SetImage(matrix_image.convert('RGB'))

try:
    print("Displaying sun. Press CTRL-C to exit.")
    while True:
        # Keeping the image displayed (you can adjust the duration)
        time.sleep(100)

except KeyboardInterrupt:
    matrix.Clear()
    print("Stopped by user.")
