from PIL import Image, ImageDraw
import math

# Global constants
# Ideal for 5x7 font size
ICON_SIZE = 14
ICON_POSITION_X = 44
ICON_POSITION_Y = 20


def init_icon():
    """Initialize a blank icon image of fixed size."""
    return Image.new("RGB", (ICON_SIZE, ICON_SIZE))


sun_icon = None


def draw_sun(canvas, rows, cols):
    """Draw a sun icon on the given canvas."""
    global sun_icon
    if sun_icon is None:
        sun_icon = create_sun_icon()
    canvas.SetImage(sun_icon, ICON_POSITION_X, ICON_POSITION_Y)


def create_sun_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    sun_center = (ICON_SIZE // 2, ICON_SIZE // 2)
    sun_radius = 3
    sun_color = (255, 255, 0)
    draw_icon.ellipse(
        [
            sun_center[0] - sun_radius,
            sun_center[1] - sun_radius,
            sun_center[0] + sun_radius,
            sun_center[1] + sun_radius
        ],
        fill=sun_color
    )
    num_rays = 8
    ray_length = 3
    ray_color = (255, 255, 0)
    for i in range(num_rays):
        angle = 360 / num_rays * i
        x_end = sun_center[0] + (sun_radius + ray_length) * \
            math.cos(math.radians(angle))
        y_end = sun_center[1] + (sun_radius + ray_length) * \
            math.sin(math.radians(angle))
        draw_icon.line((sun_center[0], sun_center[1],
                       x_end, y_end), fill=ray_color)
    return icon_image


cloud_icon = None


def draw_cloud(canvas, rows, cols):
    """Draw a cloud icon on the given canvas."""
    global cloud_icon
    if cloud_icon is None:
        cloud_icon = create_cloud_icon()
    canvas.SetImage(cloud_icon, ICON_POSITION_X, ICON_POSITION_Y)


def create_cloud_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    cloud_color = (255, 255, 255)
    sun_color = (255, 200, 0)  # A warm yellow for the sun

    # Sun parts (a circle peeping out from behind the cloud)
    sun_center = (4, 4)  # Adjust as necessary for the sun's position
    sun_radius = 2

    # Drawing the sun behind the cloud
    # Calculate the bounding box for the sun
    sun_bbox = [
        sun_center[0] - sun_radius, sun_center[1] - sun_radius,
        sun_center[0] + sun_radius, sun_center[1] + sun_radius
    ]
    draw_icon.ellipse(sun_bbox, fill=sun_color, outline=sun_color)

    # Cloud parts
    cloud_parts = [
        (3, 5, 7, 9),  # Smaller ellipse on the left top
        (5, 3, 11, 9),  # Large middle top ellipse
        (9, 5, 13, 9),  # Smaller ellipse on the right top
        (2, 7, 12, 12),  # Large bottom ellipse to round off the bottom
        (10, 7, 14, 11),  # Small ellipse on the right to extend the cloud
    ]
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)

    return icon_image


snow_icon = None


def draw_snow(canvas, rows, cols):
    """Draw a snow icon on the given canvas."""
    global snow_icon
    if snow_icon is None:
        snow_icon = create_snow_icon()
    canvas.SetImage(snow_icon, ICON_POSITION_X, ICON_POSITION_Y)


def draw_radial_snowflake(draw, center, radius=3, num_rays=8, color=(173, 216, 230)):
    """Draw a radial snowflake pattern similar to the sun example."""
    x, y = center
    for i in range(num_rays):
        angle = 360 / num_rays * i
        x_end = x + radius * math.cos(math.radians(angle))
        y_end = y + radius * math.sin(math.radians(angle))
        draw.line((x, y, x_end, y_end), fill=color)


def draw_small_cross(draw, center, size=2, color=(173, 216, 230)):
    """Draw a small 'x' shape at the specified center."""
    x, y = center
    # Draw the lines of the 'x'
    draw.line((x - size, y - size, x + size, y + size), fill=color)
    draw.line((x + size, y - size, x - size, y + size), fill=color)


def create_snow_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    cloud_color = (128, 128, 123)
    light_blue = (173, 216, 230)  # Light blue color for the snowflake

    # Define cloud parts
    cloud_parts = [
        (3, 5, 7, 9),
        (5, 3, 11, 9),
        (9, 5, 13, 9),
        (2, 7, 12, 12),
        (10, 7, 14, 11),
    ]

    # Draw cloud
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)

    # Draw a larger radial snowflake pattern
    draw_radial_snowflake(draw_icon, (11, 6), radius=4,
                          num_rays=8, color=light_blue)

    # Draw smaller 'x' shapes near the bottom of the cloud
    draw_small_cross(draw_icon, (4, 10), size=1, color=light_blue)
    draw_small_cross(draw_icon, (8, 11), size=1, color=light_blue)

    return icon_image


thunderstorm_icon = None


def draw_thunderstorm(canvas, rows, cols):
    """Draw a thunderstorm icon on the given canvas."""
    global thunderstorm_icon
    if thunderstorm_icon is None:
        thunderstorm_icon = create_thunderstorm_icon()
    canvas.SetImage(thunderstorm_icon, ICON_POSITION_X, ICON_POSITION_Y)


def create_thunderstorm_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    cloud_color = (64, 64, 64)  # Dark gray for the cloud
    lightning_color = (255, 255, 0)  # Bright yellow for the lightning

    # Cloud parts
    cloud_parts = [
        (3, 5, 7, 9),  # Smaller ellipse on the left top
        (5, 3, 11, 9),  # Large middle top ellipse
        (9, 5, 13, 9),  # Smaller ellipse on the right top
        (2, 7, 12, 12),  # Large bottom ellipse to round off the bottom
        (10, 7, 14, 11),  # Small ellipse on the right to extend the cloud
    ]

    # Draw cloud parts
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)

    # Enhanced lightning bolt with more forks
    bolt_main = [(10, 6), (10, 9), (8, 9), (11, 12), (9, 12), (12, 15)]
    bolt_fork1 = [(10, 9), (11, 8), (10, 9)]
    bolt_fork2 = [(9, 12), (10, 11), (9, 12)]

    # Draw the main part of the lightning bolt
    draw_icon.line(bolt_main, fill=lightning_color, width=2)

    # Draw forks to make the lightning bolt more intricate
    draw_icon.line(bolt_fork1, fill=lightning_color, width=1)
    draw_icon.line(bolt_fork2, fill=lightning_color, width=1)

    return icon_image


rain_icon = None


def draw_rain(canvas, rows, cols):
    """Draw a rain icon on the given canvas."""
    global rain_icon
    if rain_icon is None:
        rain_icon = create_rain_icon()
    canvas.SetImage(rain_icon, ICON_POSITION_X, ICON_POSITION_Y)


def create_rain_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    cloud_color = (128, 128, 123)
    rain_color = (173, 216, 230)  # Light blue for rain

    # Adjusted cloud parts for a more rounded appearance
    cloud_parts = [
        (3, 5, 7, 9),  # Smaller ellipse on the left top
        (5, 3, 11, 9),  # Large middle top ellipse
        (9, 5, 13, 9),  # Smaller ellipse on the right top
        (2, 7, 12, 12),  # Large bottom ellipse to round off the bottom
        (10, 7, 14, 11),  # Small ellipse on the right to extend the cloud
    ]

    # Draw cloud parts
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)

    # More pronounced rain lines
    rain_lines = [
        (4, 12, 6, 17),
        (7, 12, 9, 17),
        (10, 12, 12, 17),
        (13, 12, 15, 17),
        # Adding more rain lines for a denser appearance
        (6, 10, 8, 15),
        (9, 10, 11, 15),
        (12, 10, 14, 15),
    ]

    # Draw rain lines with increased thickness
    for line in rain_lines:
        # Increase line width for thicker raindrops
        draw_icon.line(line, fill=rain_color, width=2)

    return icon_image


fog_icon = None


def draw_fog(canvas, rows, cols):
    """Draw a fog icon on the given canvas."""
    global fog_icon
    if fog_icon is None:
        fog_icon = create_fog_icon()
    canvas.SetImage(fog_icon, ICON_POSITION_X, ICON_POSITION_Y)


def create_fog_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)

    # Base color for fog, lighter grey to suggest mist
    fog_color = (220, 220, 220)

    # Drawing horizontal lines to represent layers of fog
    # Adjusting the opacity for each line to create a gradient effect might not be directly possible
    # Instead, we'll use different shades of grey to simulate the effect
    fog_lines = [
        (0, 5, ICON_SIZE, 5),
        (0, 7, ICON_SIZE, 7),
        (0, 9, ICON_SIZE, 9),
        (0, 11, ICON_SIZE, 11),
        (0, 13, ICON_SIZE, 13),
    ]

    # Draw the fog lines
    for line in fog_lines:
        draw_icon.line(line, fill=fog_color)

    # Optionally, add a subtle gradient effect by overlaying semi-transparent lines
    # This step is more complex and might not be visible on all displays, especially LED matrices
    # If your display supports it, consider adding semi-transparent white lines here

    return icon_image
