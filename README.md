![photo of the RPI Zero Weather Clock RGB LED Matrix in action](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/blob/main/sample-photo.jpg)

# RPI Zero Weather Clock RGB LED Matrix

This project transforms a Raspberry Pi Zero into a weather clock, displaying real-time weather conditions and time on an RGB LED Matrix. It fetches weather data from a free online weather API and uses NTP (Network Time Protocol) for accurate timekeeping.

## Features

- **Accurate Time Display:** Utilizes NTP to ensure the clock displays the correct time, automatically adjusting for time zone differences and daylight saving time.
- **Live Weather Updates:** Shows current weather conditions with intuitive icons and colors, updated in real-time from OpenWeatherMap's API.
- **Adaptive Brightness:** Features automatic brightness adjustment based on the time of day, enhancing visibility and comfort.
- **Customizable Display:** Allows for extensive customization, including temperature units, text colors, and enabling/disabling the Langton's Ant animation for dynamic background activity.

## Precompiled Binary (Recommended)

The C++ binary eliminates the horizontal line flicker seen in the Python version by calling `librgbmatrix` directly without Python overhead.

```bash
# 1. Clone the repo to your install directory
git clone https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix.git
cd RPI-Zero-Weather-Clock-RGB-LED-Matrix

# 2. Configure
cp sample-config.ini config.ini
vi config.ini  # add your API key and zip code

# 3. Install service files, log directory, and system optimisations
bash deploy/install.sh

# 4. Download the precompiled ARMv6 binary
wget https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/releases/latest/download/rgb_display
chmod +x rgb_display

# 5. Enable and start
sudo systemctl enable --now rgb_display.service
```

See [BUILDING.md](BUILDING.md) to build from source (native on Pi or cross-compiled from macOS).

## Python Version

The original Python implementation (`main.py`) is preserved for community tinkering and as a reference implementation. It works on Pi Zero W — see the setup instructions below. Use `deploy/rgb_display_python.service` if you prefer it.

## Getting Started

### Prerequisites

- Raspberry Pi Zero W [with WiFi setup and SSH access ready (headless ok)](https://www.raspberrypi.com/news/raspberry-pi-imager-imaging-utility/)
  - [Adafruit RGB Matrix Bonnet for Raspberry Pi](https://www.adafruit.com/product/3211)
  - [Bonnet Installation Instructions](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/)
- [RGB LED Matrix Panel](https://www.adafruit.com/search?q=RGB+LED+Matrix+Panel) (64 x 32 recommended).
- [Power Supplies](https://www.adafruit.com/product/1466) for both Raspberry Pi + Bonnet and LED Matrix.
- [OpenWeatherMap](https://openweathermap.org/api) API key. You can use another weather API but the parsing and configuration for this project is for the Openweathermap ["current weather API" version 2.5](https://openweathermap.org/current#one)
- Active Internet Connection for NTP synchronization and weather updates.

### Hardware Setup

- **Matrix Connection:** Attach the RGB LED Matrix to the Raspberry Pi Zero using a compatible HAT or bonnet. For a step-by-step guide, see [Adafruit's LED Matrix tutorial](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi).
- **Power Requirements:** Ensure both the Raspberry Pi Zero and the LED Matrix have an adequate power supply. It's crucial for stable operation and to prevent damage.
- **LED Display**: Connect Raspberry Pi with attached bonnet to the back of the LED Matrix panel using the ribbon cable and power cables.

### Software Setup (Python version)

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix.git
    cd RPI-Zero-Weather-Clock-RGB-LED-Matrix
    ```

2. **Install Dependencies:**

    ```bash
    sudo apt-get update ; sudo apt-get install -y git python3-pip
    pip3 install -r requirements.txt

    cd matrix
    sudo make build-python
    sudo make install-python
    ```

3. **Configuration:**

    Copy `sample-config.ini` to `config.ini` and edit it to configure your weather clock.

    ```bash
    cp sample-config.ini config.ini
    vi config.ini
    ```

    Key settings to update:

    ```ini
    [Weather]
    api_key = YOUR_OPENWEATHERMAP_API_KEY
    zip_code = 10001

    [Display]
    time_format = 24
    temp_unit = F
    AUTO_BRIGHTNESS_ADJUST = True
    MIN_BRIGHTNESS = 20
    MAX_BRIGHTNESS = 60
    LANGTONS_ANT_ENABLED = False

    [NTP]
    preferred_server = pool.ntp.org
    ```

  The most important configuration settings:

 - `[Weather]`
   - `api_key`: Your OpenWeatherMap API key.
   - `zip_code`: Your local ZIP code for weather updates. [OpenWeatherMap Current Weather](https://openweathermap.org/current#zip).
 - `[Display]`
   - `time_format`: `24` or `12`.
   - `temp_unit`: `F` (Fahrenheit) or `C` (Celsius).
   - `AUTO_BRIGHTNESS_ADJUST`: `True` to ramp brightness with the sun; `False` to use `MANUAL_BRIGHTNESS`.
   - `LANGTONS_ANT_ENABLED`: Set to `True` to enable the [Langton's Ant](https://en.wikipedia.org/wiki/Langton%27s_ant) animation. Default `False` — the animation consumes high CPU on Pi Zero W.
 - `[NTP]`
   - `preferred_server`: The NTP server used for time synchronization. `pool.ntp.org` is a reliable choice ([NTP Pool Project](https://www.ntppool.org/en/)).

4. **Run the Application:**

    ```bash
    sudo python3 main.py
    ```

    `sudo` is required for direct GPIO memory access.

### Connectivity

- **Weather Updates:** Fetches the latest weather data from OpenWeatherMap every 10 minutes to display current conditions accurately.
- **NTP Synchronization:** Ensures the time displayed is precise by syncing with global NTP servers. This is vital for maintaining accurate time without manual adjustments, especially important for applications like clocks where precision is key.

## Usage

After setup, the device will display the current time and weather information. You can customize the display and update intervals by modifying the `config.ini` file, tailoring the weather clock to your preferences. Logs are written to `/var/log/rgb/weather_clock.log` for troubleshooting.

For running permanently as a display, use the service files in `deploy/`:

```bash
bash deploy/install.sh
sudo systemctl enable --now rgb_display.service       # C++ binary (recommended)
# sudo systemctl enable --now rgb_display_python.service  # Python alternative
```

## License

This project is licensed under the GPL 3.0 License - see the LICENSE file for details.

## Acknowledgments

- Weather data is provided by [OpenWeatherMap](https://openweathermap.org/api).
- Inspired by projects from the [Raspberry Pi community](https://www.raspberrypi.org/).
- [Adafruit](https://learn.adafruit.com/)
- [RGB Matrix Library Maintainer](https://github.com/hzeller)
