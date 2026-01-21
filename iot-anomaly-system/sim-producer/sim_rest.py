#!/usr/bin/env python3
import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests

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

def send_rest(api_url: str, api_key: str, ctx: DeviceContext, metrics: Dict[str, float]) -> None:
    url = api_url.rstrip("/") + "/ingest"
    payload: Dict[str, Any] = {
        "ts": utc_iso_ts(),
        "device_id": ctx.device_id,
        "location": ctx.location,
        "model": ctx.model,
        "metrics": metrics,
    }
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
    resp.raise_for_status()

def run_rest_sim(api_url: str, api_key: str, interval_sec: float = 1.0) -> None:
    devices: List[Any] = [
        TempHumidityGenerator(DeviceContext("esp32-001")),
        SoilMoistureGenerator(DeviceContext("esp32-002")),
    ]
    try:
        while True:
            for gen in devices:
                metrics = gen.next_metrics()
                send_rest(api_url, api_key, gen.ctx, metrics)
                print("REST sent", gen.ctx.device_id, metrics)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\nREST sim stopped")

def main() -> None:
    parser = argparse.ArgumentParser(description="REST simulator to ingestion-api")
    parser.add_argument("--api-url", default="http://localhost:6902", help="ingestion-api base URL")
    parser.add_argument("--api-key", default="team32-secret", help="API key for header X-API-Key")
    parser.add_argument("--interval", type=float, default=1.0, help="send interval seconds")
    args = parser.parse_args()
    run_rest_sim(args.api_url, args.api_key, args.interval)

if __name__ == "__main__":
    main()