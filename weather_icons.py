from PIL import Image, ImageDraw
import math

# Global constants
ICON_SIZE = 16
ICON_POSITION_X = 46
ICON_POSITION_Y = 19


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
    sun_radius = 5
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
    cloud_parts = [
        (5, 5, 9, 9),
        (7, 3, 11, 7),
        (10, 4, 14, 8),
        (12, 6, 16, 10)
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


def create_snow_icon():
    icon_image = init_icon()
    draw_icon = ImageDraw.Draw(icon_image)
    cloud_color = (128, 128, 123)
    snow_color = (255, 255, 255)
    snowflakes = [
        (10, 12),
        (13, 14),
        (8, 15)
    ]
    cloud_parts = [
        (5, 5, 9, 9),
        (7, 3, 11, 7),
        (10, 4, 14, 8),
        (12, 6, 16, 10)
    ]
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)
    for flake in snowflakes:
        x, y = flake
        draw_icon.point((x, y), fill=snow_color)
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
    cloud_color = (64, 64, 64)
    lightning_color = (255, 165, 0)
    cloud_parts = [
        (5, 5, 9, 9),
        (7, 3, 11, 7),
        (10, 4, 14, 8),
        (12, 6, 16, 10)
    ]
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)
    bolt_points = [
        (10, 7),
        (11, 9),
        (9, 9),
        (12, 15),
        (11, 15),
        (9, 11),
        (10, 11)
    ]
    draw_icon.polygon(bolt_points, fill=lightning_color)
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
    cloud_color = (255, 255, 255)
    rain_color = (173, 216, 230)
    rain_lines = [
        (8, 11, 10, 15),
        (11, 11, 13, 15),
        (14, 11, 16, 15)
    ]
    cloud_parts = [
        (5, 5, 9, 9),
        (7, 3, 11, 7),
        (10, 4, 14, 8),
        (12, 6, 16, 10)
    ]
    for part in cloud_parts:
        draw_icon.ellipse(part, fill=cloud_color, outline=cloud_color)
    for line in rain_lines:
        draw_icon.line(line, fill=rain_color)
    return icon_image
