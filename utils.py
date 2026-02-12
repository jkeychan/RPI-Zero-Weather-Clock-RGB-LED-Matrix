import bisect
import colorsys
import time
from typing import Tuple
from constants import TEMP_COLORS  # Fahrenheit-based gradient


def _celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit for color lookup (gradient is F-based)."""
    return (celsius * 9 / 5) + 32


def get_temp_color(temp: float, temp_unit: str = 'F') -> Tuple[int, int, int]:
    """Get RGB color for temperature. Gradient is defined in Fahrenheit."""
    if temp_unit.upper() == 'C':
        temp = _celsius_to_fahrenheit(temp)
    else:
        temp = float(temp)
    thresholds = [t.temp_threshold for t in TEMP_COLORS]
    idx = bisect.bisect_left(thresholds, temp)
    if idx >= len(TEMP_COLORS):
        return TEMP_COLORS[-1].color
    return TEMP_COLORS[idx].color


def get_color_by_time(interval_seconds: int) -> Tuple[int, int, int]:
    current_time = time.time()
    normalized_time = (current_time % interval_seconds) / interval_seconds
    r, g, b = colorsys.hsv_to_rgb(normalized_time, 1.0, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)
