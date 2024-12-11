from PIL import Image, ImageDraw
import math

# Global constants
# NOTE: Ideal for 5x7 font size, you will need to adjust these parameters for other LED Matrices
ICON_SIZE = 14
ICON_POSITION_X = 50
ICON_POSITION_Y = 20

icons = {
    "sun": None,
    "cloud": None,
    "snow": None,
    "thunderstorm": None,
    "rain": None,
    "fog": None,
}


def init_icon():
    """Initialize a blank icon image of fixed size."""
    return Image.new("RGB", (ICON_SIZE, ICON_SIZE))


def draw_sun(canvas):
    """Draw a sun icon on the given canvas."""
    if icons["sun"] is None:
        icons["sun"] = create_sun_icon()
    canvas.SetImage(icons["sun"], ICON_POSITION_X, ICON_POSITION_Y)


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


def draw_cloud(canvas):
    """Draw a cloud icon on the given canvas."""
    if icons["cloud"] is None:
        icons["cloud"] = create_cloud_icon()
    canvas.SetImage(icons["cloud"], ICON_POSITION_X, ICON_POSITION_Y)


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


def draw_snow(canvas):
    """Draw a snow icon on the given canvas."""
    if icons["snow"] is None:
        icons["snow"] = create_snow_icon()
    canvas.SetImage(icons["snow"], ICON_POSITION_X, ICON_POSITION_Y)


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


def draw_thunderstorm(canvas):
    """Draw a thunderstorm icon on the given canvas."""
    global thunderstorm_icon
    if thunderstorm_icon is None:
        thunderstorm_icon = create_thunderstorm_icon()
    canvas.SetImage(icons["thunderstorm_icon"],
                    ICON_POSITION_X, ICON_POSITION_Y)


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


def draw_rain(canvas):
    """Draw a cloud icon on the given canvas."""
    if icons["rain"] is None:
        icons["rain"] = create_rain_icon()
    canvas.SetImage(icons["rain"], ICON_POSITION_X, ICON_POSITION_Y)


def create_rain_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    rain_color = (173, 216, 230)  # Light blue for rain

    # Define teardrop-shaped raindrops with the taper at the top, moved to the left by 5 pixels
    raindrops = [
        # Raindrop 1, moved right by 1 pixel
        [(2, 2), (0, 6), (1, 7), (3, 7), (4, 6), (2, 2)],
        # Raindrop 2, narrowed by 1 column
        [(6, 1), (5, 5), (5, 6), (7, 6), (7, 5), (6, 1)],
        [(11, 2), (9, 6), (10, 7), (12, 7), (13, 6), (11, 2)],  # Raindrop 3
        # Uncomment the next line for a fourth raindrop, if desired
        # [(15, 1), (13, 5), (14, 6), (16, 6), (17, 5), (15, 1)],  # Raindrop 4
    ]

    # Draw each teardrop-shaped raindrop
    for raindrop in raindrops:
        draw_icon.polygon(raindrop, fill=rain_color, outline=rain_color)

    return icon_image


def draw_fog(canvas):
    """Draw a fog icon on the given canvas."""
    global fog_icon
    if fog_icon is None:
        fog_icon = create_fog_icon()
    canvas.SetImage(icons["fog_icon"], ICON_POSITION_X, ICON_POSITION_Y)


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
