from PIL import Image, ImageDraw
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

# Create a new image to draw the cloud and lightning icon (smaller than the main matrix)
icon_size = 16  # dimensions for the icon
icon_image = Image.new("RGB", (icon_size, icon_size))

# Parameters for the cloud and lightning
cloud_color = (64, 64, 64)  # dark gray for the cloud
lightning_color = (255, 165, 0)  # orange for the lightning bolt

# Define the cloud shape


def draw_cloud(draw_obj, cloud_color):
    cloud_parts = [
        (5, 5, 9, 9),
        (7, 3, 11, 7),
        (10, 4, 14, 8),
        (12, 6, 16, 10)
    ]
    for part in cloud_parts:
        draw_obj.ellipse(part, fill=cloud_color, outline=cloud_color)

# Define the lightning shape


def draw_lightning(draw_obj, lightning_color):
    # Points that define the zigzag shape of a lightning bolt
    bolt_points = [
        (10, 7),  # Starting at the top of the bolt
        (11, 9),  # Going slightly right
        (9, 9),   # Back towards the left
        (12, 15),  # Down to the bottom right
        (11, 15),  # Small step left to make the bottom narrower
        (9, 11),  # Up towards the middle left
        (10, 11)  # Back towards the right to complete the zigzag
    ]
    draw_obj.polygon(bolt_points, fill=lightning_color)


# Create the effect of flashing lightning
try:
    print("Displaying thunderstorm. Press CTRL-C to exit.")
    while True:
        # For each loop iteration, create a fresh image and draw context.
        icon_image = Image.new("RGB", (icon_size, icon_size))
        draw_icon = ImageDraw.Draw(icon_image)

        draw_cloud(draw_icon, cloud_color)  # Draw the cloud for each frame

        # Draw lightning (appears)
        draw_lightning(draw_icon, lightning_color)

        # Position the icon image within the larger matrix
        matrix_image = Image.new("RGB", (options.cols, options.rows))
        matrix_image.paste(icon_image, (icon_position_x, icon_position_y))

        # Display the image on the LED matrix
        matrix.SetImage(matrix_image.convert('RGB'))
        time.sleep(0.2)  # Lightning visible duration

        # Now, create a new frame without the lightning but with the cloud still present.
        icon_image_without_lightning = Image.new("RGB", (icon_size, icon_size))
        draw_icon_without_lightning = ImageDraw.Draw(
            icon_image_without_lightning)
        draw_cloud(draw_icon_without_lightning,
                   cloud_color)  # Draw the cloud only

        # Position the icon (now without lightning) within the larger matrix
        matrix_image_without_lightning = Image.new(
            "RGB", (options.cols, options.rows))
        matrix_image_without_lightning.paste(
            icon_image_without_lightning, (icon_position_x, icon_position_y))

        # Display the image (now without lightning) on the LED matrix
        matrix.SetImage(matrix_image_without_lightning.convert('RGB'))
        time.sleep(0.4)  # Lightning hidden duration

except KeyboardInterrupt:
    matrix.Clear()
    print("Stopped by user.")
