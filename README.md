# RPI Zero Weather Clock RGB LED Matrix

This project combines hardware interfacing and software development to create a weather clock using a wireless Raspberry Pi Zero and an RGB LED Matrix. The clock not only displays the current time, but also visualizes the weather conditions with the help of weather API data.

## Features

- **Time Display:** Shows the current time in a 24-hour format.
- **Weather Visualization:** Displays weather conditions using symbols and colors on the RGB LED matrix. (64 x 32 used by default)
- **Auto-Update:** Automatically updates the weather information at configurable intervals.
- **Customizable Display:** Offers options to customize the display according to user preferences.

## Getting Started

### Prerequisites

- Raspberry Pi Zero W
- RGB LED Matrix Panel (64x32 is great but you can run at different sizes and display pitches)
- Power Supply for Raspberry Pi and LED Matrix
- Internet Connection

### Hardware Setup

1. Connect your RGB LED Matrix to the Raspberry Pi Zero using the appropriate connector like a bonnet or other interface: [Adafruit Tutorials]
2. Ensure your Raspberry Pi Zero is powered correctly and has an active internet connection for weather updates.

### Software Setup

1. **Clone the Repository**

```bash
git clone https://github.com/jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix.git
cd RPI-Zero-Weather-Clock-RGB-LED-Matrix
```
2. **Install Dependencies**
```bash
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 install -r requirements.txt
```

3. **Configuration**
   Edit the config.json file to set your location, API key, and any other preferences related to the weather display.


4. **Running the Project**
```bash
python3 weather_clock.py
```

### Usage
After the initial setup, the device will start displaying the current time and weather updates. You can further customize the display settings and update intervals by modifying the config.json file.

### License
This project is licensed under the [GPL 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) License - see the LICENSE file for details.

## Acknowledgments
Weather data provided by [OpenWeatherMap](https://openweathermap.org/api)
Inspiration from [Raspberry Pi community](https://www.raspberrypi.org/) projects