# Python Performance Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix four runtime bugs, remove dead code, and deduplicate a utility function to reduce CPU usage on the Pi Zero W.

**Architecture:** All changes are targeted, in-place edits to existing files — no new files, no restructuring. The most impactful change is passing `dynamic_color` as a parameter into `draw_weather_data` rather than recomputing it every frame.

**Tech Stack:** Python 3, rpi-rgb-led-matrix Python bindings, requests, configparser

---

## File Map

| File | Change |
|------|--------|
| `main.py` | Pass `dynamic_color` param; deduplicate `time.time()` calls; drop brightness INFO log; remove thunderstorm sleep |
| `samplebase.py` | Remove dead `usleep` method |
| `weather.py` | Remove local `celsius_to_fahrenheit`; import `_celsius_to_fahrenheit` from `utils` |
| `config_loader.py` | Change `LANGTONS_ANT_ENABLED` fallback to `False` |
| `sample-config.ini` | Change `LANGTONS_ANT_ENABLED` default to `False` |

---

## Deployment reference

The app runs as a systemd service on `pi-zero-w-rgb-screen.local`:

```
ExecStart=/usr/bin/python3 /home/jeff/Documents/Code/RGB-Display/main.py --led-cols=64
WorkingDirectory=/home/jeff/Documents/Code/RGB-Display
Restart=always
```

After each deploy:
```bash
scp <changed files> jeff@pi-zero-w-rgb-screen.local:~/Documents/Code/RGB-Display/
ssh jeff@pi-zero-w-rgb-screen.local "sudo systemctl restart rgb_display.service"
ssh jeff@pi-zero-w-rgb-screen.local "sudo systemctl status rgb_display.service"
```

Check logs:
```bash
ssh jeff@pi-zero-w-rgb-screen.local "sudo tail -30 /var/log/rgb-matrix.log"
```

---

## Task 1: Remove `usleep` from `samplebase.py`

**Files:**
- Modify: `samplebase.py:34-35`

The `usleep` method is never called by this project. It exists in the upstream library samples but is dead code here.

- [ ] **Step 1: Remove the method**

In `samplebase.py`, delete lines 34–35:

```python
    def usleep(self, value):
        time.sleep(value / 1000000.0)
```

The file after the change should have `run` follow directly after `__init__`, with no `usleep` method between them.

- [ ] **Step 2: Verify syntax**

```bash
python3 -m py_compile samplebase.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add samplebase.py
git commit -m "refactor: remove unused usleep method from SampleBase"
```

---

## Task 2: Consolidate duplicate `celsius_to_fahrenheit` in `weather.py`

**Files:**
- Modify: `weather.py:24-25` (remove), `weather.py:6` (add import)

`weather.py` defines its own `celsius_to_fahrenheit` which is identical to `_celsius_to_fahrenheit` in `utils.py`. Remove the duplicate and import from `utils`.

- [ ] **Step 1: Update the import line at the top of `weather.py`**

Change:
```python
import requests
import time
import datetime
import threading
import logging
from typing import Tuple, Optional, Dict, Any
```

To:
```python
import requests
import time
import datetime
import threading
import logging
from typing import Tuple, Optional, Dict, Any
from utils import _celsius_to_fahrenheit
```

- [ ] **Step 2: Remove the local `celsius_to_fahrenheit` function**

Delete lines 24–25 in `weather.py`:

```python
def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9/5) + 32
```

- [ ] **Step 3: Update the two call sites in `fetch_weather`**

Change (lines 48–49 after deletion offset):
```python
        if temp_unit == 'F':
            temperature = int(celsius_to_fahrenheit(temperature))
            feels_like = int(celsius_to_fahrenheit(feels_like))
```

To:
```python
        if temp_unit == 'F':
            temperature = int(_celsius_to_fahrenheit(temperature))
            feels_like = int(_celsius_to_fahrenheit(feels_like))
```

- [ ] **Step 4: Verify syntax**

```bash
python3 -m py_compile weather.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add weather.py
git commit -m "refactor: remove duplicate celsius_to_fahrenheit, import from utils"
```

---

## Task 3: Change `LANGTONS_ANT_ENABLED` default to `False`

**Files:**
- Modify: `config_loader.py:61`
- Modify: `sample-config.ini:57`

The live Pi config does not set this key, so the `getboolean` fallback of `True` causes Langton's Ant to run every frame.

- [ ] **Step 1: Update fallback in `config_loader.py`**

Change line 61:
```python
        self.LANGTONS_ANT_ENABLED = self.config.getboolean(
            DISPLAY_SECTION, 'LANGTONS_ANT_ENABLED', fallback=True)
```

To:
```python
        self.LANGTONS_ANT_ENABLED = self.config.getboolean(
            DISPLAY_SECTION, 'LANGTONS_ANT_ENABLED', fallback=False)
```

- [ ] **Step 2: Update `sample-config.ini`**

Change:
```ini
# Enable Langton's Ant animation in the background
LANGTONS_ANT_ENABLED = True
```

To:
```ini
# Enable Langton's Ant animation in the background (default: False — high CPU on Pi Zero W)
LANGTONS_ANT_ENABLED = False
```

- [ ] **Step 3: Verify syntax**

```bash
python3 -m py_compile config_loader.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add config_loader.py sample-config.ini
git commit -m "perf: default LANGTONS_ANT_ENABLED to False to reduce CPU on Pi Zero W"
```

---

## Task 4: Fix `draw_weather_data` recomputing `dynamic_color` every frame

**Files:**
- Modify: `main.py:130-175` (method signature + body)
- Modify: `main.py:240-241` (call site)

The method ignores the throttled `dynamic_color` maintained in `run()` and recomputes it from scratch on every frame (~16x/sec). Fix: add it as a parameter.

- [ ] **Step 1: Add `dynamic_color` parameter to `draw_weather_data`**

Change the method signature at line 130:

```python
    def draw_weather_data(self, offscreen_canvas, font, temperature, feels_like, humidity, main_weather, weather_description, show_main_weather, scroll_pos):
```

To:

```python
    def draw_weather_data(self, offscreen_canvas, font, temperature, feels_like, humidity, main_weather, weather_description, show_main_weather, scroll_pos, dynamic_color):
```

- [ ] **Step 2: Remove the inline `dynamic_color` computation inside the method**

Inside `draw_weather_data`, remove lines 141–142:

```python
        dynamic_color = graphics.Color(
            *get_color_by_time(self.app_config.DYNAMIC_COLOR_INTERVAL_SECONDS))
```

The `dynamic_color` parameter now provides this value. The rest of the method body is unchanged.

- [ ] **Step 3: Update the call site in `run()`**

Change line 240–241:

```python
            scroll_pos = self.draw_weather_data(offscreen_canvas, font, temperature, feels_like,
                                                humidity, main_weather, weather_description, show_main_weather, scroll_pos)
```

To:

```python
            scroll_pos = self.draw_weather_data(offscreen_canvas, font, temperature, feels_like,
                                                humidity, main_weather, weather_description, show_main_weather, scroll_pos, dynamic_color)
```

- [ ] **Step 4: Verify syntax**

```bash
python3 -m py_compile main.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "perf: pass cached dynamic_color into draw_weather_data instead of recomputing each frame"
```

---

## Task 5: Fix three remaining `main.py` issues

**Files:**
- Modify: `main.py:213,215` (time.time() dedup)
- Modify: `main.py:85-87` (brightness log level)
- Modify: `main.py:127-128` (thunderstorm sleep)

Three separate one-line fixes bundled into a single commit.

- [ ] **Step 1: Deduplicate `time.time()` calls in the main loop**

In `run()`, change lines 213 and 215. The current code:

```python
            if (time.time() - last_switch_time) >= text_cycle_interval:
                show_main_weather = not show_main_weather
                last_switch_time = time.time()
```

Change to:

```python
            if (now_secs - last_switch_time) >= text_cycle_interval:
                show_main_weather = not show_main_weather
                last_switch_time = now_secs
```

(`now_secs` is already assigned at line 208 in the same loop body.)

- [ ] **Step 2: Drop brightness log from INFO to DEBUG**

In `adjust_brightness_by_time`, change:

```python
            logging.info(
                f"Manual brightness set to {manual_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
```

To:

```python
            logging.debug(
                f"Manual brightness set to {manual_brightness}% at {datetime.datetime.now().strftime('%H:%M')}")
```

- [ ] **Step 3: Remove the hardcoded thunderstorm sleep**

In `display_weather_icon`, remove lines 127–128:

```python
            if main_weather == 'Thunderstorm':
                time.sleep(0.1)
```

The method body after the change:

```python
    def display_weather_icon(self, main_weather):
        fn = WEATHER_DRAW_MAP.get(main_weather)
        if fn:
            fn(self.matrix)
```

- [ ] **Step 4: Verify syntax**

```bash
python3 -m py_compile main.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "perf: deduplicate time.time() calls; drop noisy brightness log; remove thunderstorm sleep"
```

---

## Task 6: Deploy to Pi and verify

- [ ] **Step 1: Copy changed files to the Pi**

```bash
scp main.py samplebase.py weather.py config_loader.py sample-config.ini \
    jeff@pi-zero-w-rgb-screen.local:~/Documents/Code/RGB-Display/
```

- [ ] **Step 2: Restart the service**

```bash
ssh jeff@pi-zero-w-rgb-screen.local "sudo systemctl restart rgb_display.service && sleep 5 && sudo systemctl status rgb_display.service"
```

Expected: status shows `active (running)`, no errors.

- [ ] **Step 3: Check logs for startup errors**

```bash
ssh jeff@pi-zero-w-rgb-screen.local "sudo tail -30 /var/log/rgb-matrix.log"
```

Expected: lines showing config loaded, NTP time fetched, weather thread started. No Python tracebacks.

- [ ] **Step 4: Check CPU after 60 seconds**

```bash
ssh jeff@pi-zero-w-rgb-screen.local "sleep 60 && ps aux --sort=-%cpu | head -5"
```

Expected: `main.py` CPU% noticeably lower than the pre-fix 51.7%. The Langton's Ant default change alone should account for a large portion.

- [ ] **Step 5: Visual check**

Confirm on the physical display:
- Time and day display correctly
- Weather text and scrolling description work
- Weather icon renders
- Rainbow color cycling on day/time text still works (just updated less frequently — throttled via `dynamic_color_interval_seconds`)

---

## Task 7: Open PR

- [ ] **Step 1: Push branch and open PR**

```bash
git push origin main
```

Then open a PR on GitHub (`jkeychan/RPI-Zero-Weather-Clock-RGB-LED-Matrix`) with title:

`perf: fix CPU hotspots and remove dead code (Python)`

PR description should note:
- Load average on Pi Zero W was 2.72 before; expected to drop significantly
- `LANGTONS_ANT_ENABLED` default changed to `False` — users who want it must opt in via config
- No behavior changes to weather fetching, display layout, or NTP logic
