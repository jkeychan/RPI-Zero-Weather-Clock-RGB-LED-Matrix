import requests
import time
import datetime
import threading
import logging
from typing import Tuple, Optional, Dict, Any


def start_weather_thread(global_vars: Dict[str, Any], api_key: str, zip_code: str, temp_unit: str) -> None:
    logging.info("Starting the weather data fetch thread.")
    weather_thread = threading.Thread(
        target=fetch_weather_data_periodically,
        args=("https://api.openweathermap.org/data/2.5/weather",
              zip_code, api_key, temp_unit, 600, global_vars)
    )
    weather_thread.daemon = True
    weather_thread.start()
    logging.info("Weather data fetch thread started.")


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9/5) + 32


def fetch_weather(api_endpoint: str, zip_code: str, api_key: str, temp_unit: str) -> Optional[Tuple[int, int, int, str, int, int, str]]:
    logging.debug(
        f"Fetching weather data from {api_endpoint} with zip_code={zip_code} and temp_unit={temp_unit}.")
    try:
        response = requests.get(api_endpoint, params={
            "zip": zip_code, "appid": api_key, "units": "metric"
        })
        response.raise_for_status()
        logging.info("Weather data fetched successfully.")
        weather_data = response.json()

        temperature = int(weather_data["main"]["temp"])
        feels_like = int(weather_data["main"]["feels_like"])
        humidity = int(weather_data["main"]["humidity"])
        sunrise = weather_data["sys"]["sunrise"]
        sunset = weather_data["sys"]["sunset"]
        main_weather = weather_data["weather"][0]["main"]
        weather_description = weather_data["weather"][0]["description"]

        if temp_unit == 'F':
            temperature = int(celsius_to_fahrenheit(temperature))
            feels_like = int(celsius_to_fahrenheit(feels_like))

        return temperature, feels_like, humidity, main_weather, sunrise, sunset, weather_description
    except requests.exceptions.RequestException as e:
        logging.error(
            f"Failed to get weather data from {api_endpoint} for zip_code={zip_code}: {e}")
        return None


def fetch_weather_data_periodically(
    api_endpoint: str, zip_code: str, api_key: str, temp_unit: str, interval: int, global_vars: Dict[str, Any]
) -> None:
    logging.info(
        f"Starting periodic weather data fetch every {interval} seconds.")
    backoff_seconds = 5
    max_backoff = min(300, interval)
    while True:
        start_time = datetime.datetime.now()
        weather_data = fetch_weather(
            api_endpoint, zip_code, api_key, temp_unit)
        if weather_data:
            update_global_vars(global_vars, weather_data, temp_unit)
            backoff_seconds = 5
        else:
            # exponential backoff up to max_backoff
            backoff_seconds = min(max_backoff, backoff_seconds * 2)
            logging.info(f"Weather fetch failed; backing off for {backoff_seconds}s")

        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        logging.debug(
            f"Weather data fetch and update took {elapsed_time} seconds.")
        # If success, normal interval; if failure, use backoff
        time.sleep(interval if weather_data else backoff_seconds)


def update_global_vars(global_vars: Dict[str, Any], weather_data: Tuple[int, int, int, str, int, int, str], temp_unit: str) -> None:
    temperature, feels_like, humidity, main_weather, sunrise, sunset, weather_description = weather_data

    sunrise_time_str = format_unix_time(sunrise)
    sunset_time_str = format_unix_time(sunset)

    logging.info(
        f"Updating global variables with fetched weather data: "
        f"Temperature: {temperature}°{temp_unit}, Feels Like: {feels_like}°{temp_unit}, "
        f"Humidity: {humidity}%, Main Weather: {main_weather}, Description: {weather_description}, "
        f"Sunrise: {sunrise_time_str}, Sunset: {sunset_time_str}"
    )

    global_vars.update({
        "temperature": temperature,
        "feels_like": feels_like,
        "humidity": humidity,
        "main_weather": main_weather,
        "sunrise": sunrise,
        "sunset": sunset,
        "weather_description": weather_description
    })
    global_vars["initial_weather_fetched"].set()


def format_unix_time(unix_time: int) -> str:
    return datetime.datetime.fromtimestamp(unix_time, tz=datetime.timezone.utc).astimezone(tz=None).strftime('%H:%M')
