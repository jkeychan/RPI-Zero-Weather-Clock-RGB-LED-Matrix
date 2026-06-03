import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from config_loader import initialize_global_vars
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
