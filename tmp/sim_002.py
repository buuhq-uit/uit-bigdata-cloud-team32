# sim_002.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    location: str = "lineA-zone3"
    model: str = "SIMULATOR"


class Sim002SoilMoistureGenerator:
    """
    sim-002: soil_moisture (%)
    Includes occasional anomaly injection (dry-out / spike).
    """

    def __init__(
        self,
        ctx: DeviceContext | None = None,
        base_soil: float = 35.0,
        soil_noise: float = 2.0,
        anomaly_prob: float = 0.03,
        drop_range: tuple[float, float] = (15.0, 25.0),
        spike_range: tuple[float, float] = (20.0, 35.0),
    ):
        self.ctx = ctx or DeviceContext(device_id="sim-002")
        self.base_soil = base_soil
        self.soil_noise = soil_noise
        self.anomaly_prob = anomaly_prob
        self.drop_range = drop_range
        self.spike_range = spike_range

    def next_metrics(self) -> Dict[str, float]:
        soil = self.base_soil + random.uniform(-self.soil_noise, self.soil_noise)

        if random.random() < self.anomaly_prob:
            if random.random() < 0.5:
                soil -= random.uniform(*self.drop_range)
            else:
                soil += random.uniform(*self.spike_range)

        soil = clamp(soil, 0.0, 100.0)

        return {
            "soil_moisture": round(soil, 2),
        }
