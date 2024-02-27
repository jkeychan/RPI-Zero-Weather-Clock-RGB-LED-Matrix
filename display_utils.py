# display_utils.py
from PIL import Image, ImageSequence
from rgbmatrix import graphics
import time
import os


def render_weather_image(canvas, main_weather, X_OFFSET, Y_OFFSET):
    preferred_image_extensions = ['.gif', '.ppm']
    for ext in preferred_image_extensions:
        image_path = f"./images/{main_weather.lower()}{ext}"
        if os.path.exists(image_path):
            break

    try:
        if image_path.endswith('.gif'):
            for frame in ImageSequence.Iterator(Image.open(image_path)):
                canvas.SetImage(frame.convert('RGB'), X_OFFSET, Y_OFFSET)
                # Convert to seconds
                frame_duration = frame.info['duration'] / 1000.0
                time.sleep(frame_duration)
        else:
            weather_image = Image.open(image_path)
            canvas.SetImage(weather_image, X_OFFSET, Y_OFFSET)
    except IOError as e:
        print(f"Failed to load image: {image_path}")
        return False
    return True


def draw_text(canvas, font, position, color, text):
    # assuming position is a tuple like (x, y)
    x, y = position
    graphics.DrawText(canvas, font, x, y, color, text)
