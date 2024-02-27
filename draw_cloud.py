from PIL import Image
from PIL import ImageDraw
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
# or 'regular' if you're not using Adafruit's HAT/Pi Bonnet
options.hardware_mapping = 'adafruit-hat'

matrix = RGBMatrix(options=options)

# Coordinates where you want to place the sun within the larger matrix
icon_position_x = 24  # change to position the icon
icon_position_y = 8   # change to position the icon

# Create a new image to draw the sun and cloud icon (smaller than the main matrix)
icon_size = 16  # dimensions for the icon
icon_image = Image.new("RGB", (icon_size, icon_size))
draw_icon = ImageDraw.Draw(icon_image)

# Draw the sun in the background
sun_center = (icon_size // 2, icon_size // 2)
sun_radius = 5  # appropriate for the 16x16 icon
sun_color = (255, 215, 0)  # gold color for the sun

# Draw the sun as a simple circle
draw_icon.ellipse(
    [
        sun_center[0] - sun_radius,
        sun_center[1] - sun_radius,
        sun_center[0] + sun_radius,
        sun_center[1] + sun_radius
    ],
    fill=sun_color
)

# Draw the cloud over the sun
cloud_color = (255, 255, 255)  # white color for the cloud
# Cloud parts as bounding boxes for each circle
cloud_parts = [
    (5, 5, 9, 9),
    (7, 3, 11, 7),
    (10, 4, 14, 8),
    (12, 6, 16, 10)
]

for part in cloud_parts:
    draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)

# Position the icon image within the larger matrix
matrix_image = Image.new("RGB", (options.cols, options.rows))
matrix_image.paste(icon_image, (icon_position_x, icon_position_y))

# Display the final image on the LED matrix
matrix.SetImage(matrix_image.convert('RGB'))

try:
    print("Displaying sun with a cloud. Press CTRL-C to exit.")
    while True:
        time.sleep(100)  # Keep the image displayed

except KeyboardInterrupt:
    matrix.Clear()
    print("Stopped by user.")
