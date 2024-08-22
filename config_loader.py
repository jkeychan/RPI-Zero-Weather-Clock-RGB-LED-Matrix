import configparser
import csv
import logging
import logging.handlers
import threading
import errno
import os
from typing import Dict, Tuple, Any

CONFIG_FILE = 'config.ini'
COLORS_FILE = 'colors.csv'

# Constants for config sections and keys
WEATHER_SECTION = 'Weather'
DISPLAY_SECTION = 'Display'
NTP_SECTION = 'NTP'


class AppConfig:
    def __init__(self) -> None:
        self.config = self.load_config()
        self.load_weather_config()
        self.load_display_config()
        self.load_ntp_config()
        self.colors_map = self.load_colors_from_csv(COLORS_FILE)

    def load_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        if not config.sections():
            logging.error(
                f"Configuration file {CONFIG_FILE} is missing or empty.")
        else:
            logging.info(
                f"Configuration file {CONFIG_FILE} loaded successfully.")
        return config

    def load_weather_config(self) -> None:
        self.api_key = self.config.get(WEATHER_SECTION, 'api_key')
        self.zip_code = self.config.get(WEATHER_SECTION, 'zip_code')

    def load_display_config(self) -> None:
        self.temp_unit = self.config.get(
            DISPLAY_SECTION, 'temp_unit', fallback='C')
        self.FONT_PATH = self.config.get(DISPLAY_SECTION, 'FONT_PATH')
        self.FONT_SIZE = self.config.getint(DISPLAY_SECTION, 'FONT_SIZE')
        self.BRIGHTNESS = self.config.getint(
            DISPLAY_SECTION, 'BRIGHTNESS', fallback=50)
        self.text_cycle_interval = self.config.getint(
            DISPLAY_SECTION, 'text_cycle_interval', fallback=10)
        self.LANGTONS_ANT_ENABLED = self.config.getboolean(
            DISPLAY_SECTION, 'LANGTONS_ANT_ENABLED', fallback=True)
        self.AUTO_BRIGHTNESS_ADJUST = self.config.getboolean(
            DISPLAY_SECTION, 'AUTO_BRIGHTNESS_ADJUST', fallback=True)
        self.MANUAL_BRIGHTNESS = self.config.getint(
            DISPLAY_SECTION, 'MANUAL_BRIGHTNESS', fallback=50)

    def load_ntp_config(self) -> None:
        self.preferred_server = self.config.get(
            NTP_SECTION, 'preferred_server')

    def load_colors_from_csv(self, filename: str) -> Dict[str, Tuple[int, int, int]]:
        colors = {}
        if not os.path.exists(filename):
            logging.error(f"Colors CSV file {filename} not found.")
            return colors

        try:
            with open(filename, 'r') as csvfile:
                csvreader = csv.reader(csvfile)
                next(csvreader)  # skip header if there's any
                for row in csvreader:
                    rgb_values = tuple(map(int, row[1][1:-1].split(',')))
                    colors[row[0].lower()] = rgb_values
            logging.info(f"Colors loaded successfully from {filename}.")
        except Exception as e:
            logging.error(
                f"Error loading colors from CSV file {filename}: {e}")
        return colors


def get_app_config() -> AppConfig:
    return AppConfig()


def setup_logging(log_directory: str = '/var/log/rgb', log_file: str = 'app.log', max_bytes: int = 10*1024*1024, backup_count: int = 5) -> None:
    log_path = os.path.join(log_directory, log_file)

    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
            logging.info(f"Created log directory {log_directory}.")
        except PermissionError:
            print(
                f"Permission denied: Unable to create log directory: {log_directory}")
            print("Please make sure you have the right permissions.")
            return
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    if not os.access(log_directory, os.W_OK):
        print(f"Write permission denied on the directory: {log_directory}")
        print("Please make sure you have the right permissions.")
        return

    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count
    )

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Optional console logging
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)


def initialize_global_vars() -> Dict[str, Any]:
    return {
        "temperature": None,
        "feels_like": None,
        "humidity": None,
        "main_weather": None,
        "sunrise": None,
        "sunset": None,
        "weather_description": None,
        "initial_weather_fetched": threading.Event()
    }
