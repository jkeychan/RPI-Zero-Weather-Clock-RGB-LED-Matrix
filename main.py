import time
import datetime
import logging
from rgbmatrix import graphics
import weather_icons
from config_loader import setup_logging, initialize_global_vars, get_app_config, load_config
from weather import start_weather_thread
from utils import get_temp_color, get_color_by_time
from constants import TEMP_COLORS, WIDTH, HEIGHT
from langtons_ant import LangtonsAnt
from samplebase import SampleBase
import ntplib
from time import ctime

setup_logging()
app_config = get_app_config()
config = load_config()
global_vars = initialize_global_vars()
colors_map = app_config.colors_map
start_weather_thread(global_vars, app_config.api_key,
                     app_config.zip_code, app_config.temp_unit)

# Setting the default text color
try:
    TEXT_COLOR = tuple(map(int, config['Display']['TEXT_COLOR'].split(',')))
except ValueError:
    color_name = config['Display']['TEXT_COLOR'].lower()
    if color_name in colors_map:
        TEXT_COLOR = colors_map[color_name]
    else:
        raise ValueError(f"Invalid color name: {color_name}")


class SplitDisplay(SampleBase):
    """
    A class for displaying weather information and animations on an RGB LED matrix.

    This class extends SampleBase to utilize RGB matrix functionalities, offering
    features like displaying current weather conditions, temperature, humidity,
    and a Langton's Ant simulation for dynamic background activity.

    Attributes:
        app_config (AppConfig): Configuration settings for the application, including API keys and display options.
    Methods:
        run(): Main loop for updating and displaying weather data and animations.
    """

    def __init__(self, *args, **kwargs):
        super(SplitDisplay, self).__init__(*args, **kwargs)

        # Call configuration data
        self.app_config = app_config
        # Openweathermap "Weather" API
        self.api_endpoint = "https://api.openweathermap.org/data/2.5/weather"
        # Set initial display brightness
        self.initial_brightness = self.app_config.BRIGHTNESS
        logging.info(
            f"Initial brightness set to {self.initial_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
        # Fetch NTP time once at initialization
        self.ntp_time = self.get_ntp_time(self.app_config.preferred_server)
        if self.ntp_time is None:
            self.ntp_time_offset = None
            logging.error(
                "NTP time not available, falling back to system time.")
        else:
            # Calculate the offset between NTP time and local system time
            self.ntp_time_offset = self.ntp_time - datetime.datetime.now()
            logging.info(
                f"NTP Time Correctly Fetched! Time: {self.ntp_time}% + Offset: {self.ntp_time_offset} at {datetime.datetime.now().strftime('%H:%M')}")

    def get_ntp_time(self, ntp_server):
        try:
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request(ntp_server, version=3)
            return datetime.datetime.strptime(ctime(response.tx_time), "%a %b %d %H:%M:%S %Y")
        except Exception as e:
            logging.error(f"Failed to get NTP time: {e}")
            return None

    def adjust_brightness_by_time(self):
        # Try to get NTP time, if not then use local system time
        if self.ntp_time_offset is not None:
            # Use the NTP time adjusted by the previously calculated offset
            now = datetime.datetime.now() + self.ntp_time_offset
        else:
            # Fall back to system time if NTP time was not available
            now = datetime.datetime.now()
         # If auto-adjust is turned off, use the manual brightness from the config
        if not self.app_config.AUTO_BRIGHTNESS_ADJUST:
            manual_brightness = self.app_config.MANUAL_BRIGHTNESS
            self.matrix.brightness = manual_brightness
            logging.info(
                f"Manual brightness set to {manual_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
            return  # Early return if auto-adjust is off

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

        # Adjust brightness of display based on the current time
        if one_am <= now < sunrise_time:  # 1am to sunrise
            self.matrix.brightness = 10  # 10% brightness
        elif sunrise_time <= now < nine_am:  # Sunrise to 9am
            self.matrix.brightness = 20  # 20% brightness
        elif nine_am <= now < sunset_time:  # 9am to sunset
            self.matrix.brightness = 60  # 60% brightness
        elif sunset_time <= now or now < one_am:  # Sunset to 1am
            self.matrix.brightness = 20  # 20% brightness

    def get_humidity_color(self, humidity):
        """
        Determines the color for displaying humidity based on its value.

        This method returns a color that visually represents the humidity level on the display.
        Lower humidity levels are represented with a blue color, moderate levels with green,
        and high levels with orange.

        Parameters:
            humidity (int): The current humidity level as a percentage.

        Returns:
            graphics.Color: The color corresponding to the given humidity level.
        """
        if humidity < 30:
            return graphics.Color(0, 0, 255)  # Blue for low humidity
        elif humidity < 60:
            return graphics.Color(0, 255, 0)  # Green for moderate humidity
        else:
            return graphics.Color(255, 69, 0)  # Orange for high humidity

    def display_weather_icon(self, main_weather):
        """
        Displays an appropriate weather icon on the LED matrix based on the current weather condition.

        This method selects and displays a graphical representation of the current weather condition
        (e.g., sun for clear skies, clouds, rain, snow, or thunderstorm) on the LED matrix. For
        certain conditions that might be visually intensive on the display, a brief pause is introduced
        to mitigate CPU overload.

        Parameters:
            main_weather (str): A string representing the main weather condition obtained from the
                                weather API (weather.py). Expected values are 'Clear', 'Clouds', 'Rain',
                                'Snow', and 'Thunderstorm'.

        Returns:
            None
        """
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

    def draw_weather_data(self, offscreen_canvas, font, temperature, feels_like, humidity, main_weather, weather_description, show_main_weather, scroll_pos):
        # Choose what to display based on the toggle state
        weather_text = main_weather if show_main_weather else weather_description
        # Estimate text length based on average character width
        text_length_est = len(weather_text) * 6

        # Define colors
        temperature_color = graphics.Color(
            *get_temp_color(temperature, TEMP_COLORS))
        feels_like_color = graphics.Color(
            *get_temp_color(feels_like, TEMP_COLORS))
        main_weather_color = graphics.Color(
            *colors_map.get(main_weather.lower(), (255, 255, 255)))
        humidity_color = self.get_humidity_color(humidity)

        # Get current time and day
        now = time.localtime()
        time_str = time.strftime("%H:%M", now)
        day_str = time.strftime("%a", now)
        temperature_str = "{}{}".format(temperature, self.app_config.temp_unit)
        feels_str = "{}".format(feels_like) + "|"
        humidity_str = "{}%".format(humidity)

        # Dynamic color for date and time
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

        # Decide whether to scroll based on estimated text length
        if not show_main_weather and text_length_est > 32:  # Assuming 32 pixels is your width limit
            if scroll_pos + text_length_est < 0:
                scroll_pos = offscreen_canvas.width  # Reset scroll position
            graphics.DrawText(offscreen_canvas, font, scroll_pos,
                              self.app_config.FONT_SIZE * 3, main_weather_color, weather_text)
            scroll_pos += -1  # Update scroll position for next frame
        else:
            # Display statically if within limit or showing main weather
            graphics.DrawText(offscreen_canvas, font, 2,
                              self.app_config.FONT_SIZE * 3, main_weather_color, weather_text)
            scroll_pos = offscreen_canvas.width  # Reset for potential future scrolls

        return scroll_pos  # Return updated scroll position for next iteration

    def run(self):
        font = graphics.Font()
        font.LoadFont(self.app_config.FONT_PATH)
        offscreen_canvas = self.matrix.CreateFrameCanvas()

        self.matrix.brightness = self.initial_brightness
        logging.info(
            f"Initial brightness set to {self.initial_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")

        if self.app_config.LANGTONS_ANT_ENABLED:
            langtons_ant = LangtonsAnt(WIDTH - 1, HEIGHT - 1)
            logging.info(f"Installing Ant at {WIDTH - 1} and {HEIGHT - 1}")

        show_main_weather = True
        text_cycle_interval = self.app_config.text_cycle_interval
        last_switch_time = time.time()
        scroll_pos = offscreen_canvas.width  # Initialize scroll position

        while True:
            offscreen_canvas.Clear()
            if self.app_config.LANGTONS_ANT_ENABLED:
                ant_x, ant_y, ant_color = langtons_ant.move()
                offscreen_canvas.SetPixel(ant_x, ant_y, *ant_color)

            self.adjust_brightness_by_time()

            if (time.time() - last_switch_time) >= text_cycle_interval:
                show_main_weather = not show_main_weather
                last_switch_time = time.time()
                scroll_pos = offscreen_canvas.width  # Reset scroll position on toggle

            # Fetch the latest weather data
            temperature = global_vars["temperature"]
            feels_like = global_vars["feels_like"]
            humidity = global_vars["humidity"]
            main_weather = global_vars["main_weather"]
            weather_description = global_vars.get("weather_description", "N/A")

            if temperature is None or feels_like is None or humidity is None:
                print("Weather data is not available yet. Skipping this iteration.")
                time.sleep(2)  # Wait before trying again
                continue

            # Draw weather data and update scroll position
            scroll_pos = self.draw_weather_data(offscreen_canvas, font, temperature, feels_like,
                                                humidity, main_weather, weather_description, show_main_weather, scroll_pos)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            # Draw weather icon
            self.display_weather_icon(main_weather)
            time.sleep(0.03)


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
