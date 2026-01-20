import json
from typing import Any, Dict, Optional
import threading
import paho.mqtt.client as mqtt

from core.config import KAFKA_TOPIC_RAW, DEFAULT_LOCATION, DEFAULT_MODEL
from core.time import utc_iso_ts
from core.validation import clamp

RESERVED_KEYS = {"ts", "device_id", "location", "model", "metrics", "source"}

class MQTTBridge:
    def __init__(
        self,
        app,
        host: str,
        port: int,
        topic: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.app = app
        self.host = host
        self.port = port
        self.topic = topic
        self.username = username
        self.password = password
        self.client = mqtt.Client()
        self._started = False
        self._lock = threading.Lock()

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            # Connect and start background loop
            self.client.connect(self.host, self.port, keepalive=30)
            self.client.loop_start()
            self._started = True
            print(f"[mqtt-bridge] started host={self.host}:{self.port} topic={self.topic}")

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            try:
                self.client.loop_stop()
            finally:
                self.client.disconnect()
                self._started = False
                print("[mqtt-bridge] stopped")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[mqtt-bridge] connected, subscribing:", self.topic)
            client.subscribe(self.topic)
        else:
            print(f"[mqtt-bridge] connect failed rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[mqtt-bridge] disconnected rc={rc}")

    def _on_message(self, client, userdata, msg):
        payload_raw = msg.payload.decode("utf-8", errors="replace").strip()
        try:
            obj = json.loads(payload_raw)
            if not isinstance(obj, dict):
                raise ValueError("payload is not an object")
        except Exception:
            # Wrap non-JSON as raw message
            obj = {"raw": payload_raw}

        # Extract device_id: payload first, else topic second segment
        device_id = obj.get("device_id")
        if not device_id:
            parts = msg.topic.split("/")
            device_id = parts[1] if len(parts) >= 2 else "mqtt-device"

        # Build metrics
        metrics: Dict[str, float] = {}
        if isinstance(obj.get("metrics"), dict):
            for k, v in obj["metrics"].items():
                try:
                    metrics[k] = float(v)
                except Exception:
                    pass

        # Promote common fields if present
        for k in ("temperature", "humidity", "soil_moisture"):
            if k in obj and obj[k] is not None:
                try:
                    metrics[k] = float(obj[k])
                except Exception:
                    pass

        # Clamp sensible ranges
        if "humidity" in metrics:
            metrics["humidity"] = clamp(metrics["humidity"], 0.0, 100.0)
        if "soil_moisture" in metrics:
            metrics["soil_moisture"] = clamp(metrics["soil_moisture"], 0.0, 100.0)

        # If no metrics, preserve raw
        if not metrics and "raw" in obj:
            metrics["raw"] = obj["raw"]

        msg_out: Dict[str, Any] = {
            "ts": obj.get("ts") or utc_iso_ts(),
            "device_id": device_id,
            "location": obj.get("location") or DEFAULT_LOCATION,
            "model": obj.get("model") or DEFAULT_MODEL,
            "metrics": metrics,
            "source": "ingress-mqtt",
            "topic": msg.topic,
        }

        producer = getattr(self.app.state, "producer", None)
        if not producer:
            print("[mqtt-bridge] kafka producer not ready; dropping message")
            return

        try:
            producer.send(KAFKA_TOPIC_RAW, key=device_id, value=msg_out)
            # optional flush for prompt delivery; can be tuned
            producer.flush(timeout=5)
            print(f"[mqtt-bridge] forwarded device_id={device_id} metrics={list(metrics.keys())}")
        except Exception as e:
            print(f"[mqtt-bridge] kafka send failed: {e}")