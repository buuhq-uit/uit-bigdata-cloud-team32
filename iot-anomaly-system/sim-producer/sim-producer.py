#!/usr/bin/env python3
"""
IoT Kafka Producer (modular, multi-device)
- sim-001: temperature + humidity
- sim-002: soil_moisture
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from kafka import KafkaProducer


# ----------------------------
# Config
# ----------------------------

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "iot.sensor.raw"

DEFAULT_LOCATION = "lineA-zone3"
DEFAULT_MODEL = "SIMULATOR"


# ----------------------------
# Utilities
# ----------------------------

def utc_iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ----------------------------
# Core abstraction
# ----------------------------

@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    location: str = DEFAULT_LOCATION
    model: str = DEFAULT_MODEL


class MetricGenerator:
    """Base class for device metric generators."""

    def __init__(self, ctx: DeviceContext):
        self.ctx = ctx

    def next_metrics(self) -> Dict[str, float]:
        raise NotImplementedError


class TempHumidityGenerator(MetricGenerator):
    """
    sim-001: temperature + humidity
    Includes occasional anomaly injection for temperature.
    """

    def __init__(
        self,
        ctx: DeviceContext,
        base_temp: float = 46.0,
        base_hum: float = 70.0,
        temp_noise: float = 0.5,
        hum_noise: float = 1.5,
        temp_anomaly_prob: float = 0.15,
        temp_anomaly_add_range: tuple[float, float] = (8.0, 15.0),
    ):
        super().__init__(ctx)
        self.base_temp = base_temp
        self.base_hum = base_hum
        self.temp_noise = temp_noise
        self.hum_noise = hum_noise
        self.temp_anomaly_prob = temp_anomaly_prob
        self.temp_anomaly_add_range = temp_anomaly_add_range

    def next_metrics(self) -> Dict[str, float]:
        temp = self.base_temp + random.uniform(-self.temp_noise, self.temp_noise)
        hum = self.base_hum + random.uniform(-self.hum_noise, self.hum_noise)

        # inject anomaly occasionally
        if random.random() < self.temp_anomaly_prob:
            temp += random.uniform(*self.temp_anomaly_add_range)

        return {
            "temperature": round(temp, 2),
            "humidity": round(hum, 2),
        }


class SoilMoistureGenerator(MetricGenerator):
    """
    sim-002: soil_moisture (%)
    Includes occasional anomaly injection (dry-out / spike).
    """

    def __init__(
        self,
        ctx: DeviceContext,
        base_soil: float = 35.0,
        soil_noise: float = 2.0,
        anomaly_prob: float = 0.13,
        drop_range: tuple[float, float] = (15.0, 25.0),
        spike_range: tuple[float, float] = (20.0, 35.0),
    ):
        super().__init__(ctx)
        self.base_soil = base_soil
        self.soil_noise = soil_noise
        self.anomaly_prob = anomaly_prob
        self.drop_range = drop_range
        self.spike_range = spike_range

    def next_metrics(self) -> Dict[str, float]:
        soil = self.base_soil + random.uniform(-self.soil_noise, self.soil_noise)

        # inject anomaly occasionally (dry-out or sudden spike)
        if random.random() < self.anomaly_prob:
            if random.random() < 0.5:
                soil -= random.uniform(*self.drop_range)
            else:
                soil += random.uniform(*self.spike_range)

        soil = clamp(soil, 0.0, 100.0)

        return {
            "soil_moisture": round(soil, 2),
        }


# ----------------------------
# Kafka Producer wrapper
# ----------------------------

class IoTKafkaProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8"),
            acks="all",
            linger_ms=20,
        )

    def send(self, ctx: DeviceContext, metrics: Dict[str, float]) -> None:
        payload: Dict[str, Any] = {
            "ts": utc_iso_ts(),
            "device_id": ctx.device_id,
            "location": ctx.location,
            "model": ctx.model,
            "metrics": metrics,
        }
        self.producer.send(self.topic, key=ctx.device_id, value=payload)

    def flush(self) -> None:
        self.producer.flush()

    def close(self) -> None:
        try:
            self.producer.flush()
        finally:
            self.producer.close()


# ----------------------------
# App entry
# ----------------------------

def main(
    interval_sec: float = 1.0,
    flush_every: int = 1,
) -> None:
    kafka = IoTKafkaProducer(BOOTSTRAP_SERVERS, TOPIC)

    devices: List[MetricGenerator] = [
        TempHumidityGenerator(DeviceContext(device_id="sim-001")),
        SoilMoistureGenerator(DeviceContext(device_id="sim-002")),
    ]

    tick = 0
    try:
        while True:
            tick += 1

            for gen in devices:
                metrics = gen.next_metrics()
                kafka.send(gen.ctx, metrics)
                print("sent", gen.ctx.device_id, metrics)

            if flush_every > 0 and (tick % flush_every == 0):
                kafka.flush()

            time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        kafka.close()


if __name__ == "__main__":
    main(interval_sec=1.0, flush_every=1)
