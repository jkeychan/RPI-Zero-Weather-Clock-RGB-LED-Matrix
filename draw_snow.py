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

# Create a new image to draw the cloud and snow icon (smaller than the main matrix)
icon_size = 16  # dimensions for the icon
icon_image = Image.new("RGB", (icon_size, icon_size))

# Parameters for the cloud and snow
cloud_color = (128, 128, 123)  # gray
snow_color = (255, 255, 255)  # white (snow is also white like the cloud)

# Positions of the snowflakes below the cloud (as individual pixels)
snowflakes = [
    (10, 12),  # (x, y) format
    (13, 14),
    (8, 15)
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

# Function to draw snowflakes


def draw_snowflakes(draw_obj, flakes, color):
    for flake in flakes:
        x, y = flake
        draw_obj.point((x, y), fill=color)


# Create the effect of flashing snowflakes
try:
    print("Displaying snow. Press CTRL-C to exit.")
    while True:
        # For each loop iteration, we create a fresh image and draw context.
        # This way, we start with a clean slate (no snowflakes) for each frame.
        icon_image = Image.new("RGB", (icon_size, icon_size))
        draw_icon = ImageDraw.Draw(icon_image)

        draw_cloud(draw_icon, cloud_color)  # Draw the cloud for each frame

        # Draw snowflakes (appear)
        draw_snowflakes(draw_icon, snowflakes, snow_color)

        # Position the icon image within the larger matrix
        matrix_image = Image.new("RGB", (options.cols, options.rows))
        matrix_image.paste(icon_image, (icon_position_x, icon_position_y))

        # Display the image on the LED matrix
        matrix.SetImage(matrix_image.convert('RGB'))
        time.sleep(0.5)  # Snowflakes visible duration

        # Now, we create a new frame without the snowflakes but with the cloud still present.
        icon_image_without_snowflakes = Image.new(
            "RGB", (icon_size, icon_size))
        draw_icon_without_snowflakes = ImageDraw.Draw(
            icon_image_without_snowflakes)
        draw_cloud(draw_icon_without_snowflakes,
                   cloud_color)  # Draw the cloud only

        # Position the icon (now without snowflakes) within the larger matrix
        matrix_image_without_snowflakes = Image.new(
            "RGB", (options.cols, options.rows))
        matrix_image_without_snowflakes.paste(
            icon_image_without_snowflakes, (icon_position_x, icon_position_y))

        # Display the image (now without snowflakes) on the LED matrix
        matrix.SetImage(matrix_image_without_snowflakes.convert('RGB'))
        time.sleep(0.5)  # Snowflakes hidden duration

except KeyboardInterrupt:
    matrix.Clear()
    print("Stopped by user.")
