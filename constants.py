from typing import List, Tuple, NamedTuple

# Define a NamedTuple for temperature color mapping


class TempColorRange(NamedTuple):
    temp_threshold: float
    color: Tuple[int, int, int]

# Linear interpolation between two RGB colors


def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return tuple(int(color1[i] + factor * (color2[i] - color1[i])) for i in range(3))

# Generate a smooth gradient between defined color stops


def generate_temp_color_gradient(min_temp: int, max_temp: int) -> List[TempColorRange]:
    gradient_colors = [
        (0, (0, 0, 255)),       # 0°F -> Blue
        (50, (0, 255, 255)),    # 50°F -> Cyan
        (75, (255, 255, 0)),    # 75°F -> Yellow
        (100, (255, 0, 0))      # 100°F -> Red
    ]

    temp_colors = []

    # Handle temperatures below the minimum (always blue)
    for temp in range(min_temp, 0):
        temp_colors.append(TempColorRange(temp, (0, 0, 255)))

    # Handle the gradient from 0 to 100°F
    num_steps = max_temp - min_temp
    for i in range(num_steps + 1):
        temp = min_temp + i
        # Find the appropriate gradient range
        for j in range(len(gradient_colors) - 1):
            temp1, color1 = gradient_colors[j]
            temp2, color2 = gradient_colors[j + 1]
            if temp1 <= temp <= temp2:
                factor = (temp - temp1) / (temp2 - temp1)
                color = interpolate_color(color1, color2, factor)
                temp_colors.append(TempColorRange(temp, color))
                break

    # Handle temperatures above the maximum (always red)
    for temp in range(max_temp + 1, 150):  # Adjust the upper bound as needed
        temp_colors.append(TempColorRange(temp, (255, 0, 0)))

    return temp_colors


# Generate TEMP_COLORS using the gradient
min_temp = -30  # Set a minimum temperature well below 0°F
max_temp = 100  # Maximum temperature in degrees
TEMP_COLORS: List[TempColorRange] = generate_temp_color_gradient(
    min_temp, max_temp)

# Width and height for the "ant" animation and for the text matrix
WIDTH: int = 64
HEIGHT: int = 32

# Note: temperature-to-color mapping should be accessed via utils.get_temp_color()
