import time
import datetime
import logging
from rgbmatrix import graphics
from PIL import Image, ImageSequence
import os

# Local module imports
import weather_icons
from config_loader import setup_logging, initialize_global_vars, get_app_config, load_config, AppConfig
from weather import start_weather_thread
from utils import get_temp_color, get_color_by_time
from constants import TEMP_COLORS, WIDTH, HEIGHT
from langtons_ant import LangtonsAnt
from samplebase import SampleBase

# Setup Logging
setup_logging()

# Extracting necessary information from config
app_config = get_app_config()
colors_map = app_config.colors_map

# Configuration and global variable setup
config = load_config()
global_vars = initialize_global_vars()
start_weather_thread(global_vars, app_config.api_key,
                     app_config.zip_code, app_config.temp_unit)  # Pass necessary data


# Setting the text color
try:
    TEXT_COLOR = tuple(map(int, config['Display']['TEXT_COLOR'].split(',')))
except ValueError:
    color_name = config['Display']['TEXT_COLOR'].lower()
    if color_name in colors_map:
        TEXT_COLOR = colors_map[color_name]
    else:
        raise ValueError(f"Invalid color name: {color_name}")


class SplitDisplay(SampleBase):

    def __init__(self, *args, **kwargs):
        super(SplitDisplay, self).__init__(*args, **kwargs)
        self.app_config = app_config
        # Openweathermap "Weather" API
        self.api_endpoint = "https://api.openweathermap.org/data/2.5/weather"

        self.initial_brightness = self.app_config.BRIGHTNESS

        logging.info(
            f"Initial brightness set to {self.initial_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")

    def adjust_brightness_by_time(self):
        if not self.app_config.AUTO_BRIGHTNESS_ADJUST:
            # If auto-adjust is turned off, use the manual brightness from the config.
            manual_brightness = self.app_config.MANUAL_BRIGHTNESS
            self.matrix.brightness = manual_brightness
            logging.info(
                f"Manual brightness set to {manual_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
            return  # Early return if auto-adjust is off

        now = datetime.datetime.now()
        current_hour = now.hour  # Current hour in local time

        # Safely get the value, defaulting to None if it's not there.
        sunrise = global_vars.get("sunrise")
        sunset = global_vars.get("sunset")

        if sunrise is None or sunset is None:
            print("Sunrise or sunset data is not available yet. Skipping this iteration.")
            time.sleep(2)  # Wait before trying again
            return

        # Convert sunrise and sunset from UTC to local time
        sunrise_time = datetime.datetime.fromtimestamp(sunrise)
        sunset_time = datetime.datetime.fromtimestamp(sunset)

        # Define time periods for different brightness levels
        one_am = now.replace(hour=1, minute=0, second=0, microsecond=0)
        nine_am = now.replace(hour=9, minute=0, second=0, microsecond=0)

        # Adjust brightness based on the current time
        if one_am <= now < sunrise_time:  # 1am to sunrise
            self.matrix.brightness = 10  # 10% brightness
        elif sunrise_time <= now < nine_am:  # Sunrise to 9am
            self.matrix.brightness = 20  # 20% brightness
        elif nine_am <= now < sunset_time:  # 9am to sunset
            self.matrix.brightness = 60  # 60% brightness
        elif sunset_time <= now or now < one_am:  # Sunset to 1am
            self.matrix.brightness = 20  # 20% brightness

        # Log the current brightness setting
        # logging.info(
        #    f"Auto-adjusted brightness set to {self.matrix.brightness}% at {now.strftime('%H:%M')}")

    def display_weather_icon(self, main_weather):
        if main_weather == 'Clear':
            weather_icons.draw_sun(self.matrix, HEIGHT, WIDTH)
        elif main_weather == 'Clouds':
            weather_icons.draw_cloud(self.matrix, HEIGHT, WIDTH)
        elif main_weather == 'Rain':
            weather_icons.draw_rain(self.matrix, HEIGHT, WIDTH)
        elif main_weather == 'Snow':
            weather_icons.draw_snow(self.matrix, HEIGHT, WIDTH)
        elif main_weather == 'Thunderstorm':
            weather_icons.draw_thunderstorm(self.matrix, HEIGHT, WIDTH)
            # Sleep briefly to avoid overloading the CPU
            time.sleep(0.1)

    def run(self):
        font = graphics.Font()
        font.LoadFont(self.app_config.FONT_PATH)

        offscreen_canvas = self.matrix.CreateFrameCanvas()
        # Now that we're sure the matrix is initialized, we can set the brightness.
        self.matrix.brightness = self.initial_brightness

        logging.info(
            f"Initial brightness set to {self.initial_brightness}% at {datetime.datetime.now().strftime('%H:%M')}"
        )

        # Initialize Langton's Ant instance (crawls around the display changing colors)
        langtons_ant = LangtonsAnt(WIDTH - 1, HEIGHT - 1)
        logging.info(
            f"Installing Ant at {WIDTH - 1} and {HEIGHT - 1}"
        )

        while True:
            offscreen_canvas.Clear()

            # Update and draw Langton's Ant
            ant_x, ant_y, ant_color = langtons_ant.move()
            offscreen_canvas.SetPixel(ant_x, ant_y, *ant_color)
            # logging.info(f"Ant position: {ant_x}, {ant_y}, {ant_color}")

            # Adjust the brightness (you can set conditions or get input to change the brightness as needed)
            # You could pass a value here based on some condition or input
            self.adjust_brightness_by_time()

            # Get weather data
            temperature = global_vars["temperature"]
            feels_like = global_vars["feels_like"]
            humidity = global_vars["humidity"]
            main_weather = global_vars["main_weather"]

            if temperature is None or feels_like is None or humidity is None:
                print("Weather data is not available yet. Skipping this iteration.")
                time.sleep(2)  # Wait before trying again
                continue

            # Drawing weather data with the appropriate colors
            temperature_color = graphics.Color(
                *get_temp_color(temperature, TEMP_COLORS))
            feels_like_color = graphics.Color(
                *get_temp_color(feels_like, TEMP_COLORS))
            main_weather_color = graphics.Color(
                *colors_map.get(main_weather.lower(), (255, 255, 255)))
            humidity_color = graphics.Color(255, 255, 255)  # Set to white

            # Get current time and day amd parse other time and weather values
            now = time.localtime()
            time_str = time.strftime("%H:%M", now)
            day_str = time.strftime("%a", now)
            temperature_str = "{}{}".format(
                temperature, self.app_config.temp_unit)
            feels_str = "{}".format(feels_like) + "|"
            humidity_str = "{}%".format(humidity)

            # Dynamic color changes every 60 seconds
            dynamic_color = graphics.Color(*get_color_by_time(60))

            # Drawing text on the canvas
            graphics.DrawText(offscreen_canvas, font, 2,
                              self.app_config.FONT_SIZE, dynamic_color, day_str)
            graphics.DrawText(offscreen_canvas, font, 34,
                              self.app_config.FONT_SIZE, dynamic_color, time_str)
            graphics.DrawText(offscreen_canvas, font, 2,
                              self.app_config.FONT_SIZE * 2, temperature_color, temperature_str)
            graphics.DrawText(offscreen_canvas, font, 33,
                              self.app_config.FONT_SIZE * 2, feels_like_color, feels_str)
            graphics.DrawText(offscreen_canvas, font, 49,
                              self.app_config.FONT_SIZE * 2, humidity_color, humidity_str)
            graphics.DrawText(offscreen_canvas, font, 2, self.app_config.FONT_SIZE *
                              3, main_weather_color, main_weather.capitalize())

        # TODO: Fix this function to prevent it from flickering. Use the image files option below until this works
        # Based on the weather, choose what to draw.
           # if main_weather == 'Clear':
           #     weather_icons.draw_sun(self.matrix, HEIGHT, WIDTH)
           # elif main_weather == 'Clouds':
           #     weather_icons.draw_cloud(self.matrix, HEIGHT, WIDTH)
           # elif main_weather == 'Rain':
           #     weather_icons.draw_rain(self.matrix, HEIGHT, WIDTH)
           # elif main_weather == 'Snow':
           #     weather_icons.draw_snow(self.matrix, HEIGHT, WIDTH)
           # elif main_weather == 'Thunderstorm':
           #     weather_icons.draw_thunderstorm(self.matrix, HEIGHT, WIDTH)

        # Call the subroutine to display the weather icon
         #   self.display_weather_icon(main_weather)

            # Handle weather image location
            X_OFFSET = 46  # bottom right
            Y_OFFSET = 20  # bottom right

            # Prefer GIF files to PPM image files
            preferred_image_extensions = ['.gif', '.ppm', '.bmp']
            for ext in preferred_image_extensions:
                image_path = f"./images/{main_weather.lower()}{ext}"
                if os.path.exists(image_path):
                    break

            try:
                if image_path.endswith('.gif'):
                    # Handle animated GIFs
                    for frame in ImageSequence.Iterator(Image.open(image_path)):
                        offscreen_canvas.SetImage(
                            frame.convert('RGB'), X_OFFSET, Y_OFFSET)
                        # Convert to seconds
                        frame_duration = frame.info['duration'] / 1000.0
                        time.sleep(frame_duration)
                else:
                    # Handle PPM images (or any other static image format supported by PIL)
                    weather_image = Image.open(image_path)
                    offscreen_canvas.SetImage(
                        weather_image, X_OFFSET, Y_OFFSET)
            except IOError:
                print(f"Failed to load image: {image_path}")

            # prev_weather = None

            # Draw the weather icon
            # if main_weather != prev_weather:
            #    if main_weather == 'Clear':
            #        weather_icons.draw_sun(self.matrix, HEIGHT, WIDTH)
            #    elif main_weather == 'Clouds':
            #        weather_icons.draw_cloud(self.matrix, HEIGHT, WIDTH)
            #    elif main_weather == 'Rain':
            #        weather_icons.draw_rain(self.matrix, HEIGHT, WIDTH)
            #    elif main_weather == 'Snow':
            #        weather_icons.draw_snow(self.matrix, HEIGHT, WIDTH)
            #    elif main_weather == 'Thunderstorm':
            #        weather_icons.draw_thunderstorm(self.matrix, HEIGHT, WIDTH)

            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            prev_weather = main_weather
            time.sleep(0.03)  # Update frequency in seconds


# Main execution
if __name__ == "__main__":
    logging.info("Application started")
    try:
        app = SplitDisplay()
        if (not app.process()):
            app.print_help()
    except Exception as e:
        logging.error(f"Application error: {e}")
    finally:
        logging.info("Application finished")
