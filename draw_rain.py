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
# or 'regular' if not using Adafruit's HAT/Pi Bonnet
options.hardware_mapping = 'adafruit-hat'

matrix = RGBMatrix(options=options)

# Coordinates where you want to place the icon within the larger matrix
icon_position_x = 24  # change as needed
icon_position_y = 8   # change as needed

# Create a new image to draw the cloud and rain icon (smaller than the main matrix)
icon_size = 16  # dimensions for the icon
icon_image = Image.new("RGB", (icon_size, icon_size))

# Parameters for the cloud and rain
cloud_color = (255, 255, 255)  # white
rain_color = (173, 216, 230)  # light blue

# Lower the rain below the cloud
rain_lines = [
    (8, 11, 10, 15),
    (11, 11, 13, 15),
    (14, 11, 16, 15)
]

# Function to draw the cloud


def draw_cloud(draw_obj, cloud_color):
    cloud_parts = [
        (5, 5, 9, 9),
        (7, 3, 11, 7),
        (10, 4, 14, 8),
        (12, 6, 16, 10)
    ]
    for part in cloud_parts:
        draw_obj.ellipse(part, fill=cloud_color, outline=cloud_color)

# Function to draw rain


def draw_rain(draw_obj, lines, color):
    for line in lines:
        draw_obj.line(line, fill=color)


# Create the effect of flashing rain
try:
    print("Displaying rain. Press CTRL-C to exit.")
    while True:
        # For each loop iteration, we create a fresh image and draw context.
        # This way, we start with a clean slate (no rain) for each frame.
        icon_image = Image.new("RGB", (icon_size, icon_size))
        draw_icon = ImageDraw.Draw(icon_image)

        draw_cloud(draw_icon, cloud_color)  # Draw the cloud for each frame

        # Draw rain (appears)
        draw_rain(draw_icon, rain_lines, rain_color)

        # Position the icon image within the larger matrix
        matrix_image = Image.new("RGB", (options.cols, options.rows))
        matrix_image.paste(icon_image, (icon_position_x, icon_position_y))

        # Display the image on the LED matrix
        matrix.SetImage(matrix_image.convert('RGB'))
        time.sleep(0.5)  # Rain visible duration

        # Now, we create a new frame without the rain but with the cloud still present.
        icon_image_without_rain = Image.new("RGB", (icon_size, icon_size))
        draw_icon_without_rain = ImageDraw.Draw(icon_image_without_rain)
        draw_cloud(draw_icon_without_rain, cloud_color)  # Draw the cloud only

        # Position the icon (now without rain) within the larger matrix
        matrix_image_without_rain = Image.new(
            "RGB", (options.cols, options.rows))
        matrix_image_without_rain.paste(
            icon_image_without_rain, (icon_position_x, icon_position_y))

        # Display the image (now without rain) on the LED matrix
        matrix.SetImage(matrix_image_without_rain.convert('RGB'))
        time.sleep(0.5)  # Rain hidden duration

except KeyboardInterrupt:
    matrix.Clear()
    print("Stopped by user.")
