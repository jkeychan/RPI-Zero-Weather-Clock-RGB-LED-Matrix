# MQTT Weather Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace OpenWeatherMap as the primary source for temperature, humidity, and weather condition with readings from a local MQTT broker, while keeping OWM for sunrise/sunset and other fields the sensor can't provide.

**Architecture:** New `mqtt_weather.py` module subscribes to `weather/outdoor01` in a daemon thread using `paho-mqtt`. On each message it updates `global_vars` (temperature, humidity, main_weather, mqtt_last_received) and fires the `initial_weather_fetched` event. The OWM thread continues unchanged, providing sunrise/sunset/feels_like/weather_description and acting as a natural fallback (last writer wins — MQTT publishes every ~5 min vs OWM's 10 min). The handler logic is factored into a testable `_make_on_message_handler()` factory.

**Tech Stack:** `paho-mqtt>=2.0`, `pytest` (new test runner), Python 3.9+, existing `threading`/`configparser` patterns.

---

## File Map

| Action | File | Change |
|--------|------|--------|
| Create | `mqtt_weather.py` | MQTT subscriber module |
| Create | `tests/test_mqtt_weather.py` | Unit tests for message handler |
| Modify | `requirements.txt` | Add `paho-mqtt` and `pytest` |
| Modify | `sample-config.ini` | Add `[MQTT]` section |
| Modify | `config_loader.py` | Add `MQTT_SECTION`, `load_mqtt_config()` |
| Modify | `weather.py` | Add `mqtt_last_received: None` to `initialize_global_vars()` |
| Modify | `main.py` | Import and conditionally start MQTT thread |
| Manual | DietPi shell | Install + configure Mosquitto on 10.0.0.5 |
| Manual | `include/config.h` (clock project) | Update `MQTT_BROKER` to `"10.0.0.5"` |

---

## Task 1: Set up Mosquitto on DietPi (manual)

SSH into the DietPi box at 10.0.0.5 and run these commands.

- [ ] **Install Mosquitto via dietpi-software**

```bash
dietpi-software install 119
```

When prompted, confirm the install. DietPi downloads Mosquitto from the official APT repo and creates a systemd service.

- [ ] **Configure for anonymous LAN access**

Append to `/etc/mosquitto/mosquitto.conf`:
```
listener 1883
allow_anonymous true
```

```bash
echo -e "\nlistener 1883\nallow_anonymous true" | sudo tee -a /etc/mosquitto/mosquitto.conf
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

Expected: `Active: active (running)`

- [ ] **Verify round-trip on the DietPi box itself**

```bash
mosquitto_sub -h localhost -t test -C 1 &
mosquitto_pub -h localhost -t test -m hello
```

Expected: subscriber prints `hello`.

- [ ] **Verify LAN access from your laptop**

```bash
mosquitto_pub -h 10.0.0.5 -t test -m "lan-test"
mosquitto_sub -h 10.0.0.5 -t test -C 1
```

Expected: `lan-test` received.

---

## Task 2: Add dependencies to requirements.txt

- [ ] **Add paho-mqtt and pytest**

Open `requirements.txt`. It currently contains:
```
Pillow
requests
ntplib
```

Replace with:
```
Pillow
requests
ntplib
paho-mqtt
pytest
```

- [ ] **Install and verify**

```bash
pip install -r requirements.txt
python -c "import paho.mqtt.client; print('paho-mqtt ok')"
python -c "import pytest; print('pytest ok')"
```

Expected: both lines print without error.

- [ ] **Commit**

```bash
git add requirements.txt
git commit -m "build: add paho-mqtt and pytest dependencies"
```

---

## Task 3: Add MQTT config section

- [ ] **Add `[MQTT]` section to `sample-config.ini`**

Open `sample-config.ini`. After the `[NTP]` section at the end, append:

```ini

[MQTT]
# Local MQTT broker fed by the outdoor ESP32 sensor.
# Set enabled = false to use OWM-only mode (original behavior).
# broker: LAN IP of the machine running Mosquitto.
enabled = true
broker = 10.0.0.5
port = 1883
topic = weather/outdoor01
```

- [ ] **Add loader to `config_loader.py`**

At the top of `config_loader.py`, after `NTP_SECTION = 'NTP'`, add:

```python
MQTT_SECTION = 'MQTT'
```

Inside the `AppConfig` class, add this method after `load_ntp_config`:

```python
def load_mqtt_config(self) -> None:
    self.mqtt_enabled = self.config.getboolean(MQTT_SECTION, 'enabled', fallback=False)
    self.mqtt_broker  = self.config.get(MQTT_SECTION, 'broker',  fallback='localhost')
    self.mqtt_port    = self.config.getint(MQTT_SECTION, 'port',   fallback=1883)
    self.mqtt_topic   = self.config.get(MQTT_SECTION, 'topic',  fallback='weather/outdoor01')
```

In `AppConfig.__init__`, call `self.load_mqtt_config()` after `self.load_ntp_config()`:

```python
def __init__(self) -> None:
    self.config = self.load_config()
    self.load_weather_config()
    self.load_display_config()
    self.load_ntp_config()
    self.load_mqtt_config()
```

- [ ] **Verify the module imports cleanly**

```bash
python -c "from config_loader import AppConfig; print('config_loader ok')"
```

Expected: `config_loader ok`

- [ ] **Commit**

```bash
git add sample-config.ini config_loader.py
git commit -m "config: add MQTT broker settings"
```

---

## Task 4: Add `mqtt_last_received` to global_vars

- [ ] **Edit `initialize_global_vars` in `weather.py`**

Find the function (around line 81 of `weather.py`). It currently returns:

```python
def initialize_global_vars() -> Dict[str, Any]:
    return {
        "temperature": None,
        "feels_like": None,
        "humidity": None,
        "main_weather": None,
        "sunrise": None,
        "sunset": None,
        "weather_description": None,
        "initial_weather_fetched": threading.Event(),
        "lock": threading.Lock()
    }
```

Add `"mqtt_last_received": None` before `"initial_weather_fetched"`:

```python
def initialize_global_vars() -> Dict[str, Any]:
    return {
        "temperature": None,
        "feels_like": None,
        "humidity": None,
        "main_weather": None,
        "sunrise": None,
        "sunset": None,
        "weather_description": None,
        "mqtt_last_received": None,
        "initial_weather_fetched": threading.Event(),
        "lock": threading.Lock()
    }
```

- [ ] **Verify**

```bash
python -c "from weather import initialize_global_vars; gv = initialize_global_vars(); assert 'mqtt_last_received' in gv; print('ok')"
```

Expected: `ok`

- [ ] **Commit**

```bash
git add weather.py
git commit -m "feat: add mqtt_last_received field to global_vars"
```

---

## Task 5: Create `mqtt_weather.py`

- [ ] **Write the failing tests first**

Create `tests/test_mqtt_weather.py`:

```python
import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from weather import initialize_global_vars
from mqtt_weather import _make_on_message_handler


def _msg(payload_dict):
    """Build a minimal MQTTMessage-like mock."""
    m = MagicMock()
    m.payload = json.dumps(payload_dict).encode()
    return m


def test_updates_temperature_fahrenheit():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 72.5, "humidity": 60}))
    assert gv["temperature"] == 72


def test_converts_to_celsius():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'C')
    handler(None, None, _msg({"tempF": 32.0, "humidity": 50}))
    assert gv["temperature"] == 0


def test_updates_humidity():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 70.0, "humidity": 55}))
    assert gv["humidity"] == 55


def test_updates_main_weather_when_condition_present():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 70.0, "humidity": 55, "condition": "Rain"}))
    assert gv["main_weather"] == "Rain"


def test_preserves_main_weather_when_condition_absent():
    gv = initialize_global_vars()
    gv["main_weather"] = "Clouds"
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 70.0, "humidity": 55}))
    assert gv["main_weather"] == "Clouds"


def test_sets_initial_weather_fetched_event():
    gv = initialize_global_vars()
    assert not gv["initial_weather_fetched"].is_set()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 70.0, "humidity": 55}))
    assert gv["initial_weather_fetched"].is_set()


def test_sets_mqtt_last_received_timestamp():
    gv = initialize_global_vars()
    before = time.time()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 70.0, "humidity": 55}))
    assert gv["mqtt_last_received"] is not None
    assert gv["mqtt_last_received"] >= before


def test_ignores_invalid_json():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'F')
    m = MagicMock()
    m.payload = b"not json {"
    handler(None, None, m)  # must not raise
    assert gv["temperature"] is None


def test_ignores_missing_temp_f():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"humidity": 60}))
    assert gv["temperature"] is None


def test_ignores_missing_humidity():
    gv = initialize_global_vars()
    handler = _make_on_message_handler(gv, 'F')
    handler(None, None, _msg({"tempF": 70.0}))
    assert gv["temperature"] is None
```

- [ ] **Run tests — confirm they all fail with ImportError**

```bash
pytest tests/test_mqtt_weather.py -v
```

Expected: `ImportError: cannot import name '_make_on_message_handler' from 'mqtt_weather'` (module doesn't exist yet).

- [ ] **Create `mqtt_weather.py`**

```python
import json
import logging
import time
import threading
from typing import Any, Callable, Dict

import paho.mqtt.client as mqtt


def _make_on_message_handler(
    global_vars: Dict[str, Any], temp_unit: str
) -> Callable:
    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logging.error(f"MQTT: failed to decode message: {e}")
            return

        temp_f = payload.get("tempF")
        humidity = payload.get("humidity")
        if temp_f is None or humidity is None:
            logging.warning(f"MQTT: missing required fields in payload: {list(payload.keys())}")
            return

        temperature = int(temp_f) if temp_unit == 'F' else int((temp_f - 32.0) * 5.0 / 9.0)
        condition = payload.get("condition")

        with global_vars["lock"]:
            global_vars["temperature"] = temperature
            global_vars["humidity"] = int(humidity)
            if condition is not None:
                global_vars["main_weather"] = condition
            global_vars["mqtt_last_received"] = time.time()

        global_vars["initial_weather_fetched"].set()
        logging.info(
            f"MQTT: {temperature}°{temp_unit} {int(humidity)}%RH"
            + (f" {condition}" if condition else "")
        )

    return on_message


def _run_loop(client: mqtt.Client, broker: str, port: int) -> None:
    while True:
        try:
            client.connect(broker, port, keepalive=60)
            client.loop_forever(retry_first_connection=True)
        except Exception as e:
            logging.error(f"MQTT: connection error to {broker}:{port}: {e}. Retrying in 30s")
            time.sleep(30)


def start_mqtt_weather_thread(
    global_vars: Dict[str, Any],
    broker: str,
    port: int,
    topic: str,
    temp_unit: str,
) -> None:
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"MQTT: connected to {broker}:{port}, subscribing to {topic}")
            client.subscribe(topic)
        else:
            logging.warning(f"MQTT: connect failed rc={rc}")

    def on_disconnect(client, userdata, rc):
        if rc != 0:
            logging.warning(f"MQTT: disconnected rc={rc}, will reconnect")

    client.on_connect = on_connect
    client.on_message = _make_on_message_handler(global_vars, temp_unit)
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=300)

    thread = threading.Thread(
        target=_run_loop,
        args=(client, broker, port),
        name="mqtt-weather",
        daemon=True,
    )
    thread.start()
    logging.info(f"MQTT weather thread started (broker={broker}:{port} topic={topic})")
```

- [ ] **Run tests — confirm all pass**

```bash
pytest tests/test_mqtt_weather.py -v
```

Expected: 10 tests, all `PASSED`.

- [ ] **Commit**

```bash
git add mqtt_weather.py tests/test_mqtt_weather.py
git commit -m "feat: add MQTT weather subscriber module"
```

---

## Task 6: Wire MQTT thread into `main.py`

- [ ] **Add import to `main.py`**

Find the existing imports at the top of `main.py`. After `from weather import start_weather_thread`, add:

```python
from mqtt_weather import start_mqtt_weather_thread
```

- [ ] **Start the MQTT thread after the OWM thread**

Find the line:
```python
start_weather_thread(global_vars, app_config.api_key,
                     app_config.zip_code, app_config.temp_unit)
```

Add the MQTT start immediately after:
```python
start_weather_thread(global_vars, app_config.api_key,
                     app_config.zip_code, app_config.temp_unit)

if app_config.mqtt_enabled:
    start_mqtt_weather_thread(
        global_vars,
        app_config.mqtt_broker,
        app_config.mqtt_port,
        app_config.mqtt_topic,
        app_config.temp_unit,
    )
```

- [ ] **Verify the module imports cleanly with MQTT disabled**

Set `mqtt_enabled` to false via environment (no config.ini needed for this check):

```bash
python -c "
import configparser, sys
# Simulate config with MQTT disabled
from config_loader import AppConfig
# Just verify import chain works
from mqtt_weather import start_mqtt_weather_thread
print('imports ok')
"
```

Expected: `imports ok`

- [ ] **Commit**

```bash
git add main.py
git commit -m "feat: start MQTT weather thread from main when enabled"
```

---

## Task 7: Update ESP32 clock config.h

This task is in the **e-ink-paper-clock** project, not this one.

- [ ] **Edit `include/config.h` in the clock project**

Find the line:
```cpp
#define MQTT_BROKER            "10.0.0.100"
```

Change to:
```cpp
#define MQTT_BROKER            "10.0.0.5"
```

- [ ] **Build and flash**

```bash
cd /Users/jeff/Documents/Code/Git-Managed/e-ink-paper-clock
pio run
pio run -t upload
```

Expected: zero errors, zero warnings.

- [ ] **Verify readings arrive on the DietPi broker**

From your laptop:
```bash
mosquitto_sub -h 10.0.0.5 -t 'weather/outdoor01' -v
```

Wait for the next full wake (~5 min). Expected:
```
weather/outdoor01 {"device":"sensor:74:8F:88","ts":...,"tempF":...,...}
```

- [ ] **Stop Mosquitto on the laptop**

```bash
brew services stop mosquitto
```

- [ ] **Commit the clock config change**

```bash
cd /Users/jeff/Documents/Code/Git-Managed/e-ink-paper-clock
git add include/config.h
git commit -m "config: point MQTT broker to DietPi at 10.0.0.5"
```

---

## Task 8: Add `[MQTT]` section to your local `config.ini` and verify end-to-end

- [ ] **Edit `config.ini` on the Raspberry Pi** (the LED matrix Pi, not the DietPi box)

Add the `[MQTT]` section — same as `sample-config.ini`:

```ini
[MQTT]
enabled = true
broker = 10.0.0.5
port = 1883
topic = weather/outdoor01
```

- [ ] **Run the clock application**

```bash
python main.py --led-rows=32 --led-cols=64 --led-gpio-mapping=adafruit-hat
```

(Use whatever flags your deployment uses — check `deploy/` or `Makefile` for the exact invocation.)

- [ ] **Check logs for MQTT activity**

```bash
tail -f /var/log/rgb/app.log
```

Within ~5 minutes of a sensor full wake, expect:
```
MQTT: connected to 10.0.0.5:1883, subscribing to weather/outdoor01
MQTT: 67°F 72%RH Clouds
```

Confirm the displayed temperature on the LED matrix matches the MQTT value, not OWM.

- [ ] **Verify OWM fallback still works**

Temporarily set `enabled = false` in `config.ini [MQTT]`, restart the app, and confirm OWM data still populates the display. Restore `enabled = true` when done.

---

## Task 9: Run full test suite and open PR

- [ ] **Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Commit any test fixes, then create a branch and PR if desired**

```bash
git checkout -b feature/mqtt-weather-source
git push -u origin feature/mqtt-weather-source
```
