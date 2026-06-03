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
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

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
