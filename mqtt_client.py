import logging

import paho.mqtt.client as mqtt

from gpio_controller import EnergenieGPIO
from logging_config import configure_logging


LOGGER = logging.getLogger(__name__)

BROKER = "localhost"
TOPIC = "lights/barn/set"
RECEIVER = 2

def _handle_payload(payload: str, switch: EnergenieGPIO) -> None:
    """Turn the Energenie receiver on or off based on the payload."""
    payload = payload.strip().upper()
    if payload == "ON":
        switch.turn_on()
    elif payload == "OFF":
        switch.turn_off()
    else:
        LOGGER.warning("Unknown payload for topic %s: %s", TOPIC, payload)


def on_connect(client, userdata, flags, rc):
    LOGGER.info("Connected to MQTT broker with result code %s", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    payload = msg.payload.decode(errors="ignore")
    LOGGER.info("%s -> %s", msg.topic, payload)
    _handle_payload(payload, userdata["gpio_switch"])


def main():
    configure_logging()
    gpio_switch = EnergenieGPIO(RECEIVER)
    client = mqtt.Client(userdata={"gpio_switch": gpio_switch})
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
