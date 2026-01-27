#!/usr/bin/env python3
import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import paho.mqtt.client as mqtt

DEFAULT_LOCATION = "farm-zone-1"
DEFAULT_MODEL = "ESP32"

def utc_iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    location: str = DEFAULT_LOCATION
    model: str = DEFAULT_MODEL

class TempHumidityGenerator:
    def __init__(self, ctx: DeviceContext, base_temp: float = 24.0, base_hum: float = 55.0):
        self.ctx = ctx
        self.base_temp = base_temp
        self.base_hum = base_hum

    def next_metrics(self) -> Dict[str, float]:
        import random
        temp = self.base_temp + random.uniform(-0.7, 0.7)
        hum = self.base_hum + random.uniform(-2.0, 2.0)
        return {"temperature": round(temp, 2), "humidity": round(hum, 2)}

class SoilMoistureGenerator:
    def __init__(self, ctx: DeviceContext, base_soil: float = 35.0):
        self.ctx = ctx
        self.base_soil = base_soil

    def next_metrics(self) -> Dict[str, float]:
        import random
        soil = self.base_soil + random.uniform(-3.0, 3.0)
        soil = max(0.0, min(100.0, soil))
        return {"soil_moisture": round(soil, 2)}

def create_client(host: str, port: int, username: Optional[str], password: Optional[str]) -> mqtt.Client:
    client = mqtt.Client()
    if username and password:
        client.username_pw_set(username, password)
    client.connect(host, port, keepalive=30)
    client.loop_start()
    return client

def publish_json(client: mqtt.Client, topic: str, ctx: DeviceContext, metrics: Dict[str, float]) -> None:
    msg: Dict[str, Any] = {
        "ts": utc_iso_ts(),
        "device_id": ctx.device_id,
        "location": ctx.location,
        "model": ctx.model,
        "metrics": metrics,
    }
    payload = json.dumps(msg)
    client.publish(topic, payload, qos=0, retain=False)

def run_mqtt_sim(
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    base_topic: str = "iot",
    interval_sec: float = 1.0,
) -> None:
    client = create_client(host, port, username, password)
    devices: List[Any] = [
        TempHumidityGenerator(DeviceContext("esp32-001")),
        SoilMoistureGenerator(DeviceContext("esp32-002")),
    ]
    try:
        while True:
            for gen in devices:
                metrics = gen.next_metrics()
                topic = f"{base_topic}/{gen.ctx.device_id}/telemetry"
                publish_json(client, topic, gen.ctx, metrics)
                print("MQTT sent", gen.ctx.device_id, metrics, "->", topic)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\nMQTT sim stopped")
    finally:
        client.loop_stop()
        client.disconnect()

def main() -> None:
    parser = argparse.ArgumentParser(description="MQTT simulator to Mosquitto for ingestion-api")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--username", default="iot", help="MQTT username")
    parser.add_argument("--password", default="P@sswordMQTT#2025", help="MQTT password")
    parser.add_argument("--base-topic", default="iot", help="MQTT base topic")
    parser.add_argument("--interval", type=float, default=1.0, help="send interval seconds")
    args = parser.parse_args()
    run_mqtt_sim(args.host, args.port, args.username, args.password, args.base_topic, args.interval)

if __name__ == "__main__":
    main()