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

# Apply configurable log level
try:
    logging.getLogger().setLevel(
        getattr(logging, app_config.LOG_LEVEL.upper(), logging.INFO))
except Exception:
    pass

# Start the weather fetching thread
start_weather_thread(global_vars, app_config.api_key,
                     app_config.zip_code, app_config.temp_unit)


class SplitDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(SplitDisplay, self).__init__(*args, **kwargs)
        self.app_config = app_config
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
            manual_brightness = self.app_config.MANUAL_BRIGHTNESS
            self.matrix.brightness = manual_brightness
            logging.info(
                f"Manual brightness set to {manual_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
            return

        sunrise = global_vars.get("sunrise")
        sunset = global_vars.get("sunset")
        if sunrise is None or sunset is None:
            logging.info(
                "Sunrise or sunset data not available yet; skipping brightness adjust.")
            time.sleep(2)
            return

        sunrise_time = datetime.datetime.fromtimestamp(sunrise)
        sunset_time = datetime.datetime.fromtimestamp(sunset)

        noon_time = sunrise_time + (sunset_time - sunrise_time) / 2

        min_b = self.app_config.MIN_BRIGHTNESS
        max_b = self.app_config.MAX_BRIGHTNESS
        if now < sunrise_time:
            brightness = min_b
        elif now < noon_time:
            brightness = min_b + ((max_b - min_b) * (now - sunrise_time).total_seconds() /
                                  (noon_time - sunrise_time).total_seconds())
        elif now < sunset_time:
            brightness = max_b - ((max_b - min_b) * (now - noon_time).total_seconds() /
                                  (sunset_time - noon_time).total_seconds())
        else:
            brightness = min_b

        brightness = max(min_b, min(max_b, brightness))
        self.matrix.brightness = int(brightness)

    def get_humidity_color(self, humidity):
        if humidity < 30:
            return graphics.Color(0, 0, 255)  # Blue for low humidity
        elif humidity < 60:
            return graphics.Color(0, 255, 0)  # Green for moderate humidity
        else:
            return graphics.Color(255, 69, 0)  # Orange for high humidity

    def display_weather_icon(self, main_weather):
        draw_map = {
            'Clear': weather_icons.draw_sun,
            'Clouds': weather_icons.draw_cloud,
            'Rain': weather_icons.draw_rain,
            'Snow': weather_icons.draw_snow,
            'Thunderstorm': weather_icons.draw_thunderstorm,
            'Fog': weather_icons.draw_fog,
            'Mist': weather_icons.draw_fog,
            'Haze': weather_icons.draw_fog,
        }
        fn = draw_map.get(main_weather)
        if fn:
            fn(self.matrix)
            if main_weather == 'Thunderstorm':
                time.sleep(0.1)

    def draw_weather_data(self, offscreen_canvas, font, temperature, feels_like, humidity, main_weather, weather_description, show_main_weather, scroll_pos):
        weather_text = main_weather if show_main_weather else weather_description
        text_length_est = len(weather_text) * 6

        temperature_color = graphics.Color(*get_temp_color(temperature))
        feels_like_color = graphics.Color(*get_temp_color(feels_like))

        # Set main_weather_color based on the main_weather description or use a default white color
        main_weather_color = graphics.Color(255, 255, 255)  # Default to white
        humidity_color = self.get_humidity_color(humidity)
        dynamic_color = graphics.Color(*get_color_by_time(self.app_config.DYNAMIC_COLOR_INTERVAL_SECONDS))

        now = time.localtime()
        time_str = time.strftime("%H:%M", now)
        if self.app_config.time_format == 12:
            time_str = time.strftime("%I:%M", now).lstrip('0')
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

        if not show_main_weather and text_length_est > offscreen_canvas.width:
            if scroll_pos + text_length_est < 0:
                scroll_pos = offscreen_canvas.width  # Reset scroll position
            graphics.DrawText(offscreen_canvas, font, scroll_pos,
                              self.app_config.FONT_SIZE * 3, main_weather_color, weather_text)
            scroll_pos -= 1  # Update scroll position for next frame
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
        # Already logged at init; avoid duplicate log

        if self.app_config.LANGTONS_ANT_ENABLED:
            langtons_ant = LangtonsAnt(WIDTH - 1, HEIGHT - 1)
            logging.info(f"Installing Ant at {WIDTH - 1} and {HEIGHT - 1}")

        show_main_weather = True
        text_cycle_interval = self.app_config.text_cycle_interval
        last_switch_time = time.time()
        scroll_pos = offscreen_canvas.width  # Initialize scroll position

        last_brightness_update = 0.0
        last_dynamic_update = 0.0
        dynamic_color = graphics.Color(*get_color_by_time(self.app_config.DYNAMIC_COLOR_INTERVAL_SECONDS))
        frame_interval = max(20, self.app_config.FRAME_INTERVAL_MS) / 1000.0

        while True:
            offscreen_canvas.Clear()
            if self.app_config.LANGTONS_ANT_ENABLED:
                ant_x, ant_y, ant_color = langtons_ant.move()
                offscreen_canvas.SetPixel(ant_x, ant_y, *ant_color)

            now_secs = time.time()
            if now_secs - last_brightness_update >= self.app_config.BRIGHTNESS_UPDATE_SECONDS:
                self.adjust_brightness_by_time()
                last_brightness_update = now_secs

            if (time.time() - last_switch_time) >= text_cycle_interval:
                show_main_weather = not show_main_weather
                last_switch_time = time.time()
                scroll_pos = offscreen_canvas.width  # Reset scroll position on toggle

            # Safely snapshot weather values under lock
            with global_vars["lock"]:
                temperature = global_vars["temperature"]
                feels_like = global_vars["feels_like"]
                humidity = global_vars["humidity"]
                main_weather = global_vars["main_weather"]
                weather_description = global_vars.get(
                    "weather_description", "N/A")

            if temperature is None or feels_like is None or humidity is None:
                logging.info("Weather data not available yet; skipping frame.")
                time.sleep(2)
                continue

            # Update dynamic color at most once per configured interval
            if now_secs - last_dynamic_update >= self.app_config.DYNAMIC_COLOR_INTERVAL_SECONDS:
                dynamic_color = graphics.Color(*get_color_by_time(self.app_config.DYNAMIC_COLOR_INTERVAL_SECONDS))
                last_dynamic_update = now_secs

            scroll_pos = self.draw_weather_data(offscreen_canvas, font, temperature, feels_like,
                                                humidity, main_weather, weather_description, show_main_weather, scroll_pos)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            self.display_weather_icon(main_weather)
            time.sleep(frame_interval)


if __name__ == "__main__":
    logging.info("Application started")
    try:
        app = SplitDisplay()
        # Optionally wait briefly for first weather fetch to avoid early empty frames
        global_vars["initial_weather_fetched"].wait(timeout=15)
        if (not app.process()):
            app.print_help()
    except Exception as e:
        logging.error(f"Application error: {e}")
    finally:
        logging.info("Application finished")
