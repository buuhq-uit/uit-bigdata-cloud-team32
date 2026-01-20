import os

APP_NAME = "iot-ingress-rest-api"
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "iot.sensor.raw")
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "farm-zone-1")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "ESP32")
API_KEY = os.getenv("API_KEY", "team32-secret")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

# MQTT bridge config
def _as_bool(v: str | None, default: bool = True) -> bool:
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")

MQTT_ENABLE = _as_bool(os.getenv("MQTT_ENABLE"), True)
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")  # set in compose
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")  # set in compose
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/#")