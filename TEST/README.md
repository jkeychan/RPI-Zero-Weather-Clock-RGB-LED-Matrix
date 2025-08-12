C++ test port (experimental)

This folder contains an experimental C++ implementation of the weather clock using the C++ API of rpi-rgb-led-matrix. It mirrors the Python app's behavior while running as a compiled binary on Raspberry Pi.

Features
- NTP-like time via system clock; optional SNTP offset planned
- OpenWeatherMap fetch in a background thread (libcurl)
- Auto brightness based on sunrise/sunset with configurable min/max
- 12/24h time, temp color mapping, and simple weather icons
- Optional Langton's Ant animation
- Configurable frame interval and throttled updates for low CPU (Pi Zero friendly)

Prerequisites (on Raspberry Pi)
- Build and install the C++ matrix library in `matrix/` (this repo submodule)
  - cd matrix
  - sudo make build-python
  - sudo make install-python
- Dev dependencies
  - sudo apt-get update
  - sudo apt-get install -y g++ make libcurl4-openssl-dev

Build
- cd TEST && make
  - produces `./weather_clock`

Run (sudo required for GPIO)
- sudo ./weather_clock --led-cols=64 --led-rows=32

Configuration
- Copy `test-config.ini.sample` to `test-config.ini` and edit values.

Reference
- Upstream C example: c-example.c
  - https://github.com/c-base/rpi-rgb-led-matrix/blob/master/examples-api-use/c-example.c

