# sim_001.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    location: str = "lineA-zone3"
    model: str = "SIMULATOR"


class Sim001TempHumidityGenerator:
    """
    sim-001: temperature + humidity
    Includes occasional anomaly injection for temperature.
    """

    def __init__(
        self,
        ctx: DeviceContext | None = None,
        base_temp: float = 46.0,
        base_hum: float = 70.0,
        temp_noise: float = 0.5,
        hum_noise: float = 1.5,
        temp_anomaly_prob: float = 0.05,
        temp_anomaly_add_range: tuple[float, float] = (8.0, 15.0),
    ):
        self.ctx = ctx or DeviceContext(device_id="sim-001")
        self.base_temp = base_temp
        self.base_hum = base_hum
        self.temp_noise = temp_noise
        self.hum_noise = hum_noise
        self.temp_anomaly_prob = temp_anomaly_prob
        self.temp_anomaly_add_range = temp_anomaly_add_range

    def next_metrics(self) -> Dict[str, float]:
        temp = self.base_temp + random.uniform(-self.temp_noise, self.temp_noise)
        hum = self.base_hum + random.uniform(-self.hum_noise, self.hum_noise)

        if random.random() < self.temp_anomaly_prob:
            temp += random.uniform(*self.temp_anomaly_add_range)

        return {
            "temperature": round(temp, 2),
            "humidity": round(hum, 2),
        }
