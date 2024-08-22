import colorsys
import time
from typing import Tuple
from constants import TEMP_COLORS  # Import the TEMP_COLORS from constants.py


def get_temp_color(temp: float) -> Tuple[int, int, int]:
    for max_temp, color in TEMP_COLORS:
        if temp <= max_temp:
            return color
    return (255, 255, 255)  # Default to white if no match found


def get_color_by_time(interval_seconds: int) -> Tuple[int, int, int]:
    current_time = time.time()
    normalized_time = (current_time % interval_seconds) / interval_seconds
    r, g, b = colorsys.hsv_to_rgb(normalized_time, 1.0, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)
