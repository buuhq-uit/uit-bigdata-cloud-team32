import os

APP_NAME = "iot-ingress-rest-api"
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "iot.sensor.raw")
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "farm-zone-1")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "ESP32")
API_KEY = os.getenv("API_KEY", "team32-secret")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")