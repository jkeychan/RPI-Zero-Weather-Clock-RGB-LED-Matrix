# Constants and static data definitions

TEMP_COLORS = [
    # Cooler colors for lower temperatures
    (5, (64, 0, 128)),      # Dark Purple for -5 to 5F
    (10, (75, 0, 130)),     # Indigo for 5-10F
    (15, (106, 90, 205)),   # Slate Blue for 10-15F
    (20, (0, 0, 255)),      # Blue for 15-20F
    (25, (0, 191, 255)),    # Deep Sky Blue for 20-25F
    (30, (135, 206, 250)),  # Light Sky Blue for 25-30F
    (35, (0, 255, 255)),    # Cyan/Aqua for 30-35F
    (40, (0, 255, 128)),    # Spring Green for 35-40F
    (45, (173, 255, 47)),   # Green Yellow for 40-45F
    (50, (154, 205, 50)),   # Yellow Green for 45-50F
    (55, (107, 142, 35)),   # Olive Drab for 50-55F
    (60, (85, 107, 47)),    # Dark Olive Green for 55-60F
    (65, (50, 205, 50)),    # Lime Green for 60-65F
    (70, (0, 128, 0)),      # Green for 65-70F
    (75, (255, 255, 0)),    # Yellow for 70-75F
    (80, (255, 165, 0)),    # Orange for 75-80F
    (85, (255, 69, 0)),     # Orange Red for 80-85F
    (90, (255, 0, 0)),      # Red for 85-90F
    (95, (255, 99, 71)),    # Tomato for 90-95F
    (100, (255, 20, 147)),  # Deep Pink for 95-100F
    (float('inf'), (255, 0, 255))  # Magenta/Fuchsia for temperatures above 100F
]

# Width and height for the "ant" animation
WIDTH = 64
HEIGHT = 32

# Delay for the "ant" animation
ANT_DELAY_MS = 100

# You can add any other constants that your program requires here.
