# Python Performance Fixes — Design Spec

**Date:** 2026-04-08  
**Scope:** Python-only optimizations and dead-code removal (PR 1 of 2)  
**Out of scope:** C++ port, OS upgrade, frame rate changes, weather thread restructuring

---

## Context

The Pi Zero W is running the Python clock at 51.7% CPU with a load average of 2.72 on a single-core system. Three structural bugs in the main render loop are responsible for most of the unnecessary work, plus there is dead code and a duplicate utility function across the codebase.

---

## Changes

### 1. Fix: `dynamic_color` recomputed every frame (`main.py`)

**Problem:** `draw_weather_data` calls `get_color_by_time()` directly on line 141–142, invoking `colorsys.hsv_to_rgb` and `time.time()` ~16 times per second. The throttled `dynamic_color` computed in `run()` (lines 235–238) is never passed into `draw_weather_data` — the method ignores it and recomputes its own.

**Fix:** Add `dynamic_color` as a parameter to `draw_weather_data`. Remove the inline `get_color_by_time()` call inside the method. The caller in `run()` passes the already-throttled value.

### 2. Fix: `time.time()` called three times per loop iteration (`main.py`)

**Problem:** Line 208 stores `now_secs = time.time()`, but lines 213 and 215 call `time.time()` again independently, making three syscalls per frame.

**Fix:** Replace lines 213 and 215 with `now_secs`.

### 3. Fix: INFO log on every brightness update when auto is off (`main.py`)

**Problem:** `adjust_brightness_by_time` logs at INFO level every call when `AUTO_BRIGHTNESS_ADJUST = False`, causing a `RotatingFileHandler` write every 10 seconds indefinitely.

**Fix:** Change to `logging.debug`.

### 4. Fix: Hardcoded 100ms sleep during Thunderstorm frames (`main.py`)

**Problem:** `display_weather_icon` calls `time.sleep(0.1)` after drawing the thunderstorm icon. This silently adds 100ms to every frame when conditions are Thunderstorm, halving the effective frame rate with no warning.

**Fix:** Remove the `time.sleep(0.1)` entirely.

### 5. Remove dead code: `usleep` (`samplebase.py`)

**Problem:** `usleep` is defined in `SampleBase` but never called by `main.py` or `SplitDisplay`. It exists in the upstream library samples but is dead code for this project.

**Fix:** Remove the method.

### 6. Remove duplicate: `celsius_to_fahrenheit` (`weather.py`)

**Problem:** `weather.py` defines its own `celsius_to_fahrenheit` which is identical to `_celsius_to_fahrenheit` in `utils.py`.

**Fix:** Remove `celsius_to_fahrenheit` from `weather.py`. Import `_celsius_to_fahrenheit` from `utils` and use it in `fetch_weather`.

### 7. Default `LANGTONS_ANT_ENABLED` to `False` (`config_loader.py`, `sample-config.ini`)

**Problem:** The fallback value in `config_loader.py` is `True`, and the Pi's live `config.ini` does not set this key. Langton's Ant runs every frame as a result, adding a grid lookup and pixel write per iteration.

**Fix:** Change the `getboolean` fallback to `False`. Update `sample-config.ini` to match.

---

## Files changed

| File | Change |
|------|--------|
| `main.py` | Fixes 1–4 |
| `samplebase.py` | Fix 5 |
| `weather.py` | Fix 6 |
| `config_loader.py` | Fix 7 |
| `sample-config.ini` | Fix 7 |

**Not changed:** `constants.py`, `weather_icons.py`, `utils.py`, `langtons_ant.py`, `TEST/`

---

## Deploy note

The live Pi config (`~/Documents/Code/RGB-Display/config.ini`) is missing `FRAME_INTERVAL_MS`, `BRIGHTNESS_UPDATE_SECONDS`, `DYNAMIC_COLOR_INTERVAL_SECONDS`, `MIN_BRIGHTNESS`, and `MAX_BRIGHTNESS`. These fall back to coded defaults correctly. After this PR merges, the Pi config should be updated to explicitly set these keys from `sample-config.ini` to make the configuration transparent.

---

## Expected outcome

- Eliminates ~16 unnecessary `colorsys.hsv_to_rgb` + `time.time()` calls per second
- Eliminates ~3 redundant syscalls per frame loop iteration
- Removes periodic disk writes from INFO brightness logging
- Removes silent 100ms frame stalls during thunderstorm conditions
- Removes Langton's Ant from default config (biggest single CPU contributor on live system)
- Cleans duplicate conversion function and dead `usleep` method
