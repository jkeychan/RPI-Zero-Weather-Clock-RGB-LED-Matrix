# config_loader.py

import configparser
import csv
import logging
import threading
import errno
import os

CONFIG_FILE = 'config.ini'


class AppConfig:
    def __init__(self):
        config = load_config()
        self.api_key = config['Weather']['api_key']
        self.zip_code = config['Weather']['zip_code']
        self.temp_unit = config['Display']['temp_unit']
        self.FONT_PATH = config['Display']['FONT_PATH']
        self.FONT_SIZE = int(config['Display']['FONT_SIZE'])
        self.BRIGHTNESS = config.getint('Display', 'BRIGHTNESS', fallback=50)
        self.preferred_server = config['NTP']['preferred_server']
        self.text_cycle_interval = config.getint(
            'Display', 'text_cycle_interval', fallback=10)
        self.colors_map = load_colors_from_csv('colors.csv')
        self.LANGTONS_ANT_ENABLED = config.getboolean(
            'Display', 'LANGTONS_ANT_ENABLED', fallback=True)

        # Brightness adjustment
        # We use standard Python data conversion because 'getboolean' and 'getint' belong to ConfigParser, not to the dictionary object.
        self.AUTO_BRIGHTNESS_ADJUST = config.getboolean(
            'Display', 'AUTO_BRIGHTNESS_ADJUST', fallback=True)
        self.MANUAL_BRIGHTNESS = config.getint(
            'Display', 'MANUAL_BRIGHTNESS', fallback=50)


def get_app_config():
    return AppConfig()


def setup_logging():
    log_directory = '/var/log/rgb'
    log_file = 'app.log'

    # Create target Directory if it doesn't exist
    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except PermissionError:
            print(
                f"Permission denied: Unable to create log directory: {log_directory}")
            print("Please make sure you have the right permissions.")
            return
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    # Check if we have write permissions in the directory
    if not os.access(log_directory, os.W_OK):
        print(f"Write permission denied on the directory: {log_directory}")
        print("Please make sure you have the right permissions.")
        return

    log_path = os.path.join(log_directory, log_file)
    logging.basicConfig(filename=log_path, filemode='a',
                        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


def load_colors_from_csv(filename):
    colors = {}
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # skip header if there's any
        for row in csvreader:
            # Convert "(R,G,B)" to (R, G, B)
            rgb_values = tuple(map(int, row[1][1:-1].split(',')))
            colors[row[0].lower()] = rgb_values
    return colors


def initialize_global_vars():
    return {
        "temperature": None,
        "feels_like": None,
        "humidity": None,
        "main_weather": None,
        "initial_weather_fetched": threading.Event()
    }
