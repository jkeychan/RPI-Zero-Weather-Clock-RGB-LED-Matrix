# Constants and static data definitions

TEMP_COLORS = [
    # Extreme cold and below
    (0, (255, 255, 255)),  # White for 0F and below
    # Cooler colors for lower temperatures
    (5, (150, 0, 255)),    # Purple for 0-5F
    (10, (75, 0, 130)),    # Indigo for 5-10F
    (15, (0, 0, 255)),     # Blue for 10-15F
    (20, (65, 105, 225)),  # Royal Blue for 15-20F
    (25, (100, 149, 237)),  # Cornflower Blue for 20-25F
    (30, (135, 206, 250)),  # Light Sky Blue for 25-30F
    (39, (173, 216, 230)),  # Light Blue for 30-39F
    # Green range for moderate temperatures
    (40, (0, 128, 0)),     # Green for 40-44F
    (45, (34, 139, 34)),   # Forest Green for 45-49F
    (50, (60, 179, 113)),  # Medium Sea Green for 50-54F
    (55, (154, 205, 50)),  # Yellow Green for 55-59F
    (60, (173, 255, 47)),  # Green Yellow for 60-64F
    # Warming yellow gradient
    (65, (255, 255, 0)),   # Yellow for 65-69F
    (70, (255, 215, 0)),   # Gold for 70-74F
    # Orange to red gradient for higher temperatures
    (75, (255, 165, 0)),   # Orange for 75-79F
    (80, (255, 140, 0)),   # Dark Orange for 80-84F
    (85, (255, 69, 0)),    # Orange Red for 85-89F
    (90, (255, 0, 0)),     # Red for 90-94F
    (95, (214, 69, 0)),    # Red Orange for 95-99F
    (100, (255, 0, 0)),    # Bright Red for 100-104F
    (float('inf'), (255, 0, 0))  # Bright Red for temperatures above 105F
]

# Width and height for the "ant" animation
WIDTH = 64
HEIGHT = 32

# Delay for the "ant" animation
ANT_DELAY_MS = 100

# You can add any other constants that your program requires here.
