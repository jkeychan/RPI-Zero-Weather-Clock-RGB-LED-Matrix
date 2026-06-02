# MQTT Weather Source Design

**Date:** 2026-06-02
**Project:** RPI-Zero-Weather-Clock-RGB-LED-Matrix
**Status:** Ready for implementation

---

## Goal

Replace OpenWeatherMap as the primary source for temperature, humidity, and weather condition with a local MQTT broker fed by the ESP32 outdoor sensor. OWM continues to provide fields the sensor cannot supply (sunrise, sunset, feels_like, weather_description). If the MQTT sensor goes offline, OWM's next poll naturally restores those fields.

---

## Architecture

### Data flow

```
ESP32 sensor → LoRa → ESP32 clock → MQTT publish → Mosquitto broker
                                                          ↓
                                                   mqtt_weather.py (subscriber thread)
                                                          ↓
                                                    global_vars
                                                          ↑
                                              weather.py (OWM thread — unchanged)
```

### Last-writer-wins

Both the MQTT thread and the OWM thread write to `global_vars["temperature"]`, `["humidity"]`, and `["main_weather"]`. MQTT publishes every ~5 min; OWM polls every 10 min. MQTT dominates by recency in steady state. When the sensor is offline for >10 min, OWM's next poll fills in those values — no explicit staleness logic required.

OWM-only fields (sunrise, sunset, feels_like, weather_description) continue to come exclusively from OWM.

### Initial render gate

`global_vars["initial_weather_fetched"]` is a `threading.Event` that main.py waits on before rendering. Both the MQTT thread (on first message) and the OWM thread set this event — whichever arrives first unblocks rendering. On a LAN with a live sensor this will typically be MQTT (seconds after startup vs OWM's first HTTP fetch).

---

## New File: `mqtt_weather.py`

Single public function: `start_mqtt_weather_thread(global_vars, broker, port, topic, temp_unit)`.

Spawns a daemon thread running `paho-mqtt`'s `loop_forever(retry_first_connection=True)` with automatic reconnect on broker restart (`reconnect_delay_set(1, 300)`).

**On each MQTT message:**
1. Parse JSON payload (`{"device", "ts", "tempF", "humidity", "pressureInHg", "dewptF", "battPct", "condition"}`)
2. Convert `tempF` → display unit: if `temp_unit == 'F'` store as `int(tempF)`; if `'C'` convert via `(tempF - 32) * 5/9`
3. Under `global_vars["lock"]`: update `temperature`, `humidity`, `main_weather` (from `condition` if present)
4. Set `global_vars["mqtt_last_received"] = time.time()`
5. Call `global_vars["initial_weather_fetched"].set()`

**Error handling:** JSON decode errors and missing required fields (`tempF`, `humidity`) are logged and skipped. Connection errors trigger automatic reconnect via paho's built-in backoff (1–300 s). The thread never raises to the caller.

**Compile guard:** The module is only started if `app_config.mqtt_enabled` is true. With it disabled, behavior is identical to today.

---

## Config Changes

### `sample-config.ini` — new section

```ini
[MQTT]
# Local MQTT broker. Set enabled = false to use OWM-only mode.
enabled = true
broker = 10.0.0.5
port = 1883
topic = weather/outdoor01
```

### `config_loader.py` — new loader method

```python
MQTT_SECTION = 'MQTT'

def load_mqtt_config(self) -> None:
    self.mqtt_enabled = self.config.getboolean(MQTT_SECTION, 'enabled', fallback=False)
    self.mqtt_broker  = self.config.get(MQTT_SECTION, 'broker', fallback='localhost')
    self.mqtt_port    = self.config.getint(MQTT_SECTION, 'port', fallback=1883)
    self.mqtt_topic   = self.config.get(MQTT_SECTION, 'topic', fallback='weather/outdoor01')
```

Called from `__init__` after `load_ntp_config()`.

---

## `global_vars` Changes

`initialize_global_vars()` in `weather.py` gains one key:

```python
"mqtt_last_received": None,   # float epoch or None — set by mqtt_weather.py
```

---

## `main.py` Changes

```python
from mqtt_weather import start_mqtt_weather_thread

# After start_weather_thread(...):
if app_config.mqtt_enabled:
    start_mqtt_weather_thread(
        global_vars,
        app_config.mqtt_broker,
        app_config.mqtt_port,
        app_config.mqtt_topic,
        app_config.temp_unit,
    )
```

---

## DietPi Broker Migration

### Install Mosquitto on DietPi (10.0.0.5)

```bash
# On the DietPi box:
dietpi-software install 119
```

DietPi installs Mosquitto from the official APT repo and creates a systemd service.

### Configure for anonymous LAN access

Edit `/etc/mosquitto/mosquitto.conf` — append:
```
listener 1883
allow_anonymous true
```

```bash
systemctl restart mosquitto
```

Verify:
```bash
mosquitto_pub -h localhost -t test -m hello
mosquitto_sub -h localhost -t test -C 1
```

### Migrate the ESP32 clock

In `include/config.h` on the clock project, update:
```cpp
#define MQTT_BROKER  "10.0.0.5"
```

Reflash. Confirm readings appear in `mosquitto_sub -h 10.0.0.5 -t 'weather/outdoor01' -v` from another machine.

### Stop laptop Mosquitto (optional)

```bash
brew services stop mosquitto
```

---

## Dependencies

Add to `requirements.txt`:
```
paho-mqtt
```

Install on the Pi:
```bash
pip install paho-mqtt
# or, if using the project's deploy workflow:
# handled by requirements.txt install step
```

---

## Invariants

- `mqtt_weather.py` never writes to `sunrise`, `sunset`, `feels_like`, or `weather_description` — those remain OWM-only
- `mqtt_weather.py` never calls `initial_weather_fetched.wait()` — only `.set()`
- `weather.py` is not modified except for adding `mqtt_last_received: None` to `initialize_global_vars()`
- `ENABLE_MQTT false` (or `[MQTT] enabled = false`) → zero code change in rendering path
