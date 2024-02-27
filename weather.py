import requests
import time
import datetime
import threading
import logging
from config_loader import load_config


def start_weather_thread(global_vars, api_key, zip_code, temp_unit):
    config = load_config()
    api_key = config['Weather']['api_key']
    zip_code = config['Weather']['zip_code']
    temp_unit = config['Display']['temp_unit']

    weather_thread = threading.Thread(target=fetch_weather_data_periodically, args=(
        "https://api.openweathermap.org/data/2.5/weather", zip_code, api_key, temp_unit, 600, global_vars))
    weather_thread.daemon = True
    weather_thread.start()


def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32


def fetch_weather(api_endpoint, zip_code, api_key, temp_unit):
    try:
        response = requests.get(api_endpoint, params={
                                "zip": zip_code, "appid": api_key, "units": "metric"})
        response.raise_for_status()
        weather_data = response.json()
        temperature = int(weather_data["main"]["temp"])
        feels_like = int(weather_data["main"]["feels_like"])
        humidity = int(weather_data["main"]["humidity"])
        sunrise = weather_data["sys"]["sunrise"]
        sunset = weather_data["sys"]["sunset"]
        main_weather = weather_data["weather"][0]["main"]

        if temp_unit == 'F':
            temperature = int(celsius_to_fahrenheit(temperature))
            feels_like = int(celsius_to_fahrenheit(feels_like))

        return temperature, feels_like, humidity, main_weather, sunrise, sunset
    except requests.exceptions.RequestException as e:
        logging.error("Failed to get weather data:", e)
        return None, None, None, None, None, None


def fetch_weather_data_periodically(api_endpoint, zip_code, api_key, temp_unit, interval, global_vars):
    while True:
        try:
            temperature, feels_like, humidity, main_weather, sunrise, sunset = fetch_weather(
                api_endpoint, zip_code, api_key, temp_unit)

            if temperature is not None:
                # Convert Unix time to readable string (only hours and minutes)
                sunrise_time_str = datetime.datetime.fromtimestamp(
                    sunrise, tz=datetime.timezone.utc).astimezone(tz=None).strftime('%H:%M')
                sunset_time_str = datetime.datetime.fromtimestamp(
                    sunset, tz=datetime.timezone.utc).astimezone(tz=None).strftime('%H:%M')

                logging.info(
                    f"Weather fetched successfully: Temperature {temperature}, Feels Like {feels_like}, Humidity {humidity}, Main Weather {main_weather}, Sunrise {sunrise_time_str}, Sunset {sunset_time_str}")
                global_vars["temperature"] = temperature
                global_vars["feels_like"] = feels_like
                global_vars["humidity"] = humidity
                global_vars["main_weather"] = main_weather
                global_vars["sunrise"] = sunrise  # store sunrise time
                global_vars["sunset"] = sunset    # store sunset time
                global_vars["initial_weather_fetched"].set()
        except Exception as e:
            logging.error(f"Failed to fetch weather data: {e}")

        time.sleep(interval)  # wait before fetching the data again
