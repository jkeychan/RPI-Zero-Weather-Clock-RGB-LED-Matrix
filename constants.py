import os
import csv
from typing import List, Tuple, NamedTuple, Dict

# Define a NamedTuple for temperature color mapping


class TempColorRange(NamedTuple):
    temp_threshold: float
    color: Tuple[int, int, int]

# Load colors from the CSV file


def load_colors_from_csv(filename: str) -> Dict[str, Tuple[int, int, int]]:
    colors = {}
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Colors CSV file {filename} not found.")

    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # skip header
        for row in csvreader:
            color_name = row[0].strip().lower().replace(" ", "_")
            try:
                # Properly handle the RGB tuple by joining the split elements and then evaluating the string
                rgb_values = tuple(map(int, row[1].strip("() ").split(',')))
                colors[color_name] = rgb_values
            except ValueError as e:
                print(f"Error processing row: {row}. Error: {e}")
                continue  # Skip this row if there's an error

    return colors


# Load colors from the CSV file (update the path if necessary)
colors_map = load_colors_from_csv('colors.csv')

# Define TEMP_COLORS using the loaded colors
TEMP_COLORS: List[TempColorRange] = [
    TempColorRange(0, colors_map['white']),
    TempColorRange(5, colors_map['purple']),
    TempColorRange(10, colors_map['indigo']),
    TempColorRange(15, colors_map['blue']),
    TempColorRange(20, colors_map['royal_blue']),
    TempColorRange(25, colors_map['cornflower_blue']),
    TempColorRange(30, colors_map['light_sky_blue']),
    TempColorRange(39, colors_map['light_blue']),
    TempColorRange(40, colors_map['green']),
    TempColorRange(45, colors_map['forest_green']),
    TempColorRange(50, colors_map['medium_sea_green']),
    TempColorRange(55, colors_map['yellow_green']),
    TempColorRange(60, colors_map['green_yellow']),
    TempColorRange(65, colors_map['yellow']),
    TempColorRange(70, colors_map['gold']),
    TempColorRange(75, colors_map['orange']),
    TempColorRange(80, colors_map['dark_orange']),
    TempColorRange(85, colors_map['orange_red']),
    TempColorRange(90, colors_map['red']),
    TempColorRange(95, colors_map['orange_red']),
    TempColorRange(100, colors_map['red']),
    TempColorRange(float('inf'), colors_map['red']),
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
    return colors_map['red']  # Default to RED if no range matches
