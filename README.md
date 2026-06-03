![photo of the RPI Zero Weather Clock RGB LED Matrix in action](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/blob/main/sample-photo.jpg)

# RPI Zero Weather Clock RGB LED Matrix

[![Build](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/actions/workflows/release.yml/badge.svg)](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/actions/workflows/release.yml)
[![Lint](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/actions/workflows/lint.yml/badge.svg)](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/actions/workflows/lint.yml)
[![CodeQL](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/actions/workflows/codeql.yml/badge.svg)](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix?logo=github)](https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Zero%20W-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/products/raspberry-pi-zero-w/)
[![C++17](https://img.shields.io/badge/C%2B%2B-17-00599C?logo=cplusplus&logoColor=white)](src/weather_clock.cc)
[![MQTT](https://img.shields.io/badge/MQTT-optional-8A2BE2)](https://mosquitto.org/)

A Raspberry Pi Zero weather clock that displays real-time weather and time on a 64×32 RGB LED Matrix. Weather data comes from OpenWeatherMap and, optionally, a local MQTT sensor that overrides the cloud reading with live indoor/outdoor measurements.

The project ships two fully functional implementations:

| | C++ (`src/weather_clock.cc`) | Python (`main.py`) |
|---|---|---|
| **Status** | Production (recommended) | Reference / community tinkering |
| **Flicker** | None — librgbmatrix called directly | Occasional horizontal line flicker (Python GIL) |
| **CPU (Pi Zero W)** | ~38% | ~43% |
| **MQTT support** | Yes (`libmosquitto`) | Yes (`paho-mqtt`) |

---

## Quick Start (C++ binary)

```bash
# 1. Clone
git clone https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix.git
cd RPI-Zero-Weather-Clock-RGB-LED-Matrix

# 2. Configure
cp sample-config.ini config.ini
vi config.ini  # set api_key and zip_code at minimum

# 3. Install service, log directory, and system tuning
bash deploy/install.sh

# 4. Download the precompiled ARMv6 binary
wget https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix/releases/latest/download/rgb_display
chmod +x rgb_display

# 5. Start
sudo systemctl enable --now rgb_display.service
```

See [BUILDING.md](BUILDING.md) to build from source (native on Pi or cross-compiled from macOS).

---

## Features

- **Accurate time** via NTP, with automatic timezone and DST handling
- **Live weather** — temperature, feels-like, humidity, condition icon, scrolling description
- **Two weather sources** — OpenWeatherMap (cloud, every 10 min) and optional local MQTT sensor (every ~5 min); last write wins, so the sensor reading is always fresh
- **Adaptive brightness** — smooth solar interpolation between configurable min/max brightness
- **Temperature colors** — smooth blue→red gradient mapped to Celsius value
- **Langton's Ant** optional background animation (high CPU — disabled by default on Pi Zero W)
- **12 or 24-hour** time format

---

## Hardware

- Raspberry Pi Zero W (WiFi + SSH; [headless setup](https://www.raspberrypi.com/news/raspberry-pi-imager-imaging-utility/))
- [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211) ([wiring guide](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/))
- 64×32 RGB LED Matrix Panel ([Adafruit search](https://www.adafruit.com/search?q=RGB+LED+Matrix+Panel))
- 5V power supply for the Pi + a separate 5V supply for the matrix
- [OpenWeatherMap](https://openweathermap.org/api) free API key

---

## Configuration

Copy `sample-config.ini` to `config.ini` and edit it. The file is not tracked by git.

```ini
[Weather]
api_key = YOUR_OPENWEATHERMAP_API_KEY
zip_code = 10001

[Display]
time_format = 24          # 12 or 24
temp_unit = F             # F or C
AUTO_BRIGHTNESS_ADJUST = True
MIN_BRIGHTNESS = 20       # percent
MAX_BRIGHTNESS = 60
LANGTONS_ANT_ENABLED = False

[NTP]
preferred_server = pool.ntp.org

[MQTT]
# Optional — set enabled = false to use OpenWeatherMap only (original behavior)
enabled = false
broker = 192.168.1.x      # LAN IP of your Mosquitto broker
port = 1883
topic = weather/outdoor01
```

### MQTT weather source

When `enabled = true`, a background thread subscribes to the configured topic and updates temperature, humidity, and (optionally) weather condition whenever the sensor publishes. OpenWeatherMap continues running in parallel and provides sunrise/sunset, feels-like, and weather description — fields a bare sensor typically cannot provide.

Expected payload format (fields your sensor should publish):

```json
{"tempF": 72.5, "humidity": 60, "condition": "Clear"}
```

- `tempF` and `humidity` are required. The binary ignores messages that omit either.
- `condition` is optional. If absent, the OWM-derived condition is preserved.
- Temperature is converted to Celsius internally regardless of `temp_unit`; the display shows whichever unit you configured.

**Broker setup** — any Mosquitto broker on your LAN works. Quick setup on a DietPi or Raspberry Pi:

```bash
# Install
sudo apt install mosquitto mosquitto-clients -y

# Allow anonymous LAN access (append to /etc/mosquitto/mosquitto.conf)
echo -e "\nlistener 1883\nallow_anonymous true" | sudo tee -a /etc/mosquitto/mosquitto.conf
sudo systemctl restart mosquitto

# Verify
mosquitto_pub -h localhost -t weather/outdoor01 -m '{"tempF":72.5,"humidity":60}'
mosquitto_sub -h localhost -t weather/outdoor01 -C 1
```

**C++ dependency** — the MQTT feature requires `libmosquitto` at runtime. If you build from source:

```bash
sudo apt install libmosquitto-dev -y
make
```

The precompiled binary already links against `libmosquitto`. If the library is missing on your Pi, install it:

```bash
sudo apt install libmosquitto1 -y
```

**Python dependency** — the Python version uses `paho-mqtt`, which is already in `requirements.txt`.

---

## C++ version

### Building from source (native on Pi)

```bash
sudo apt install libcurl4-openssl-dev libmosquitto-dev -y
make
```

The first build clones and compiles the `rpi-rgb-led-matrix` submodule (~2 min on Pi Zero W). Subsequent builds are fast.

Output binary: `./rgb_display`

### How it works

`src/weather_clock.cc` is a single-file C++17 application. On startup it:

1. Reads `config.ini` from the working directory
2. Initialises the RGB matrix via `librgbmatrix` and drops OS privileges (GPIO setup requires root; the display loop does not)
3. Starts `WeatherThread` — polls OpenWeatherMap every 600 s with exponential backoff on failure
4. If `mqtt_enabled = true`, starts `MqttWeatherThread` — subscribes to the broker topic and updates weather state on every incoming message
5. Waits up to 15 s for the first weather reading (from whichever source arrives first)
6. Runs the display loop — reads weather state under a mutex, renders the frame, swaps the canvas on VSync

Both weather threads write to the same `WeatherState` struct (atomics + mutex). MQTT publishes every ~5 minutes; OWM every 10 minutes. The display always shows the most recently written value.

Logs are written to `/var/log/rgb/weather_clock.log` and rotate at 1 MB.

### systemd service

`deploy/install.sh` installs `rgb_display.service`. The service runs from `/home/jeff/Documents/Code/RGB-Display/` by default — update `WorkingDirectory` and `ExecStart` in the unit file if your install path differs.

After updating the binary:

```bash
sudo systemctl stop rgb_display.service
sudo cp rgb_display /path/to/install/rgb_display
sudo systemctl start rgb_display.service
```

**Log file ownership** — the service drops to the `daemon` user after initialising the matrix hardware. If the log file is owned by root, subsequent log writes will be silently dropped. Ensure the log file is writable by daemon:

```bash
sudo chown daemon:daemon /var/log/rgb/weather_clock.log
```

---

## Python version

The original Python implementation is preserved in `main.py` for community tinkering and as a readable reference. It has feature parity with the C++ version including MQTT support.

### Setup

```bash
sudo apt-get update && sudo apt-get install -y git python3-pip
pip3 install -r requirements.txt

cd matrix
sudo make build-python
sudo make install-python
cd ..

cp sample-config.ini config.ini
vi config.ini
```

### Run

```bash
sudo python3 main.py
```

Or as a service:

```bash
sudo systemctl enable --now rgb_display_python.service
```

---

## Logs

Both versions log to `/var/log/rgb/weather_clock.log`:

```
[2026-06-03 12:12:13] [INFO] rgb_display starting
[2026-06-03 12:12:13] [INFO] Matrix initialized: 64x32 slowdown=3
[2026-06-03 12:12:14] [INFO] MQTT thread started, connecting to 192.168.1.x:1883 topic=weather/outdoor01
[2026-06-03 12:12:14] [INFO] MQTT connected, subscribing to weather/outdoor01
[2026-06-03 12:12:45] [INFO] MQTT update: 57°F 100%RH Clear
```

---

## License

GPL 3.0 — see [LICENSE](LICENSE).

## Acknowledgments

- Weather data: [OpenWeatherMap](https://openweathermap.org/api)
- RGB matrix library: [hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix)
- Inspired by the [Raspberry Pi community](https://www.raspberrypi.org/) and [Adafruit](https://learn.adafruit.com/)
