from typing import List, Tuple, NamedTuple

# Color constants
WHITE = (255, 255, 255)
PURPLE = (150, 0, 255)
INDIGO = (75, 0, 130)
BLUE = (0, 0, 255)
ROYAL_BLUE = (65, 105, 225)
CORN_FLOWER_BLUE = (100, 149, 237)
LIGHT_SKY_BLUE = (135, 206, 250)
LIGHT_BLUE = (173, 216, 230)
GREEN = (0, 128, 0)
FOREST_GREEN = (34, 139, 34)
MEDIUM_SEA_GREEN = (60, 179, 113)
YELLOW_GREEN = (154, 205, 50)
GREEN_YELLOW = (173, 255, 47)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
DARK_ORANGE = (255, 140, 0)
ORANGE_RED = (255, 69, 0)
RED = (255, 0, 0)
RED_ORANGE = (214, 69, 0)

# Define a NamedTuple for temperature color mapping


class TempColorRange(NamedTuple):
    temp_threshold: float
    color: Tuple[int, int, int]


# List of temperature ranges and their corresponding colors
TEMP_COLORS: List[TempColorRange] = [
    TempColorRange(0, WHITE),                # Extreme cold and below
    # Cooler colors for lower temperatures
    TempColorRange(5, PURPLE),
    TempColorRange(10, INDIGO),
    TempColorRange(15, BLUE),
    TempColorRange(20, ROYAL_BLUE),
    TempColorRange(25, CORN_FLOWER_BLUE),
    TempColorRange(30, LIGHT_SKY_BLUE),
    TempColorRange(39, LIGHT_BLUE),
    # Green range for moderate temperatures
    TempColorRange(40, GREEN),
    TempColorRange(45, FOREST_GREEN),
    TempColorRange(50, MEDIUM_SEA_GREEN),
    TempColorRange(55, YELLOW_GREEN),
    TempColorRange(60, GREEN_YELLOW),
    TempColorRange(65, YELLOW),              # Warming yellow gradient
    TempColorRange(70, GOLD),
    # Orange to red gradient for higher temperatures
    TempColorRange(75, ORANGE),
    TempColorRange(80, DARK_ORANGE),
    TempColorRange(85, ORANGE_RED),
    TempColorRange(90, RED),
    TempColorRange(95, RED_ORANGE),
    TempColorRange(100, RED),
    # Bright Red for temperatures above 105F
    TempColorRange(float('inf'), RED)
]

# Width and height for the "ant" animation and for the text matrix
WIDTH: int = 64
HEIGHT: int = 32

# Function to get color based on temperature


def get_temp_color(temperature: float) -> Tuple[int, int, int]:
    """Returns the color corresponding to the given temperature."""
    for temp_color_range in TEMP_COLORS:
        if temperature <= temp_color_range.temp_threshold:
            return temp_color_range.color
    return RED  # Default to RED if no range matches
