import time
import datetime
import logging
from rgbmatrix import graphics
import weather_icons
from config_loader import setup_logging, initialize_global_vars, get_app_config
from weather import start_weather_thread
from utils import get_temp_color, get_color_by_time
from constants import WIDTH, HEIGHT
from langtons_ant import LangtonsAnt
from samplebase import SampleBase
import ntplib
from time import ctime

# Setup logging and load configuration
setup_logging()
app_config = get_app_config()
global_vars = initialize_global_vars()
colors_map = app_config.colors_map

# Start the weather fetching thread
start_weather_thread(global_vars, app_config.api_key,
                     app_config.zip_code, app_config.temp_unit)


class SplitDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(SplitDisplay, self).__init__(*args, **kwargs)
        self.app_config = app_config
        self.api_endpoint = "https://api.openweathermap.org/data/2.5/weather"
        self.initial_brightness = self.app_config.BRIGHTNESS
        logging.info(
            f"Initial brightness set to {self.initial_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
        self.ntp_time = self.get_ntp_time(self.app_config.preferred_server)
        if self.ntp_time is None:
            self.ntp_time_offset = None
            logging.error(
                "NTP time not available, falling back to system time.")
        else:
            self.ntp_time_offset = self.ntp_time - datetime.datetime.now()
            logging.info(
                f"NTP Time Correctly Fetched! Time: {self.ntp_time} + Offset: {self.ntp_time_offset} at {datetime.datetime.now().strftime('%H:%M')}")

    def get_ntp_time(self, ntp_server):
        try:
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request(ntp_server, version=3)
            return datetime.datetime.strptime(ctime(response.tx_time), "%a %b %d %H:%M:%S %Y")
        except Exception as e:
            logging.error(f"Failed to get NTP time: {e}")
            return None

    def adjust_brightness_by_time(self, test_time=None):
        now = test_time or (datetime.datetime.now(
        ) + self.ntp_time_offset if self.ntp_time_offset else datetime.datetime.now())
        if not self.app_config.AUTO_BRIGHTNESS_ADJUST:
            manual_brightness = self.app_config.BRIGHTNESS
            self.matrix.brightness = manual_brightness
            logging.info(
                f"Manual brightness set to {manual_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
            return

        sunrise = global_vars.get("sunrise")
        sunset = global_vars.get("sunset")
        if sunrise is None or sunset is None:
            print("Sunrise or sunset data is not available yet. Skipping this iteration.")
            time.sleep(2)
            return

        sunrise_time = datetime.datetime.fromtimestamp(sunrise)
        sunset_time = datetime.datetime.fromtimestamp(sunset)

        noon_time = sunrise_time + (sunset_time - sunrise_time) / 2

        if now < sunrise_time:
            brightness = 20  # Before sunrise: 20% brightness
        elif now < noon_time:
            brightness = 20 + (40 * (now - sunrise_time).total_seconds() /
                               (noon_time - sunrise_time).total_seconds())
        elif now < sunset_time:
            brightness = 60 - (40 * (now - noon_time).total_seconds() /
                               (sunset_time - noon_time).total_seconds())
        else:
            brightness = 20  # After sunset: 20% brightness

        brightness = max(20, min(60, brightness))
        self.matrix.brightness = int(brightness)

    def get_humidity_color(self, humidity):
        if humidity < 30:
            return graphics.Color(0, 0, 255)  # Blue for low humidity
        elif humidity < 60:
            return graphics.Color(0, 255, 0)  # Green for moderate humidity
        else:
            return graphics.Color(255, 69, 0)  # Orange for high humidity

    def display_weather_icon(self, main_weather):
        if main_weather == 'Clear':
            weather_icons.draw_sun(self.matrix)
        elif main_weather == 'Clouds':
            weather_icons.draw_cloud(self.matrix)
        elif main_weather == 'Rain':
            weather_icons.draw_rain(self.matrix)
        elif main_weather == 'Snow':
            weather_icons.draw_snow(self.matrix)
        elif main_weather == 'Thunderstorm':
            weather_icons.draw_thunderstorm(self.matrix)
            time.sleep(0.1)

    def draw_weather_data(self, offscreen_canvas, font, temperature, feels_like, humidity, main_weather, weather_description, show_main_weather, scroll_pos):
        weather_text = main_weather if show_main_weather else weather_description
        text_length_est = len(weather_text) * 6

        temperature_color = graphics.Color(*get_temp_color(temperature))
        feels_like_color = graphics.Color(*get_temp_color(feels_like))
        main_weather_color = graphics.Color(
            *colors_map.get(main_weather.lower(), (255, 255, 255)))
        humidity_color = self.get_humidity_color(humidity)
        dynamic_color = graphics.Color(*get_color_by_time(60))

        now = time.localtime()
        time_str = time.strftime("%H:%M", now)
        day_str = time.strftime("%a", now)
        temperature_str = "{}{}".format(temperature, self.app_config.temp_unit)
        feels_str = "{}".format(feels_like) + "|"
        humidity_str = "{}%".format(humidity)

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

        if not show_main_weather and text_length_est > 32:  # Assuming 32 pixels is your width limit
            if scroll_pos + text_length_est < 0:
                scroll_pos = offscreen_canvas.width  # Reset scroll position
            graphics.DrawText(offscreen_canvas, font, scroll_pos,
                              self.app_config.FONT_SIZE * 3, main_weather_color, weather_text)
            scroll_pos += -1  # Update scroll position for next frame
        else:
            graphics.DrawText(offscreen_canvas, font, 2,
                              self.app_config.FONT_SIZE * 3, main_weather_color, weather_text)
            scroll_pos = offscreen_canvas.width  # Reset for potential future scrolls

        return scroll_pos

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

            temperature = global_vars["temperature"]
            feels_like = global_vars["feels_like"]
            humidity = global_vars["humidity"]
            main_weather = global_vars["main_weather"]
            weather_description = global_vars.get("weather_description", "N/A")

            if temperature is None or feels_like is None or humidity is None:
                print("Weather data is not available yet. Skipping this iteration.")
                time.sleep(2)
                continue

            scroll_pos = self.draw_weather_data(offscreen_canvas, font, temperature, feels_like,
                                                humidity, main_weather, weather_description, show_main_weather, scroll_pos)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            self.display_weather_icon(main_weather)
            time.sleep(0.03)


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
