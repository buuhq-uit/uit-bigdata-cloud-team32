#!/usr/bin/env python3
"""Vibration and accelerometer signal generators"""
import time
import math
from typing import Dict
from .base import BaseGenerator, DeviceContext, _noise, _maybe_spike

class MachineVibrationGenerator(BaseGenerator):
    """Simulate vibration sensor (3-axis accelerometer + RMS)"""
    def __init__(self, ctx: DeviceContext, base_rms_g: float = 0.2):
        super().__init__(ctx)
        self.base_rms_g = base_rms_g
    
    def next_metrics(self) -> Dict[str, float]:
        t = time.time()
        # Simulate multi-frequency vibration
        ax = 0.1 * math.sin(2 * math.pi * 2.0 * t) + _noise(0.02)
        ay = 0.1 * math.sin(2 * math.pi * 1.2 * t + 0.5) + _noise(0.02)
        az = 0.1 * math.sin(2 * math.pi * 0.8 * t + 1.1) + _noise(0.02)
        rms = math.sqrt(ax*ax + ay*ay + az*az)
        # Inject anomaly: sudden spike
        rms = _maybe_spike(rms, 0.01, 4.0)
        return {
            "accel_x_g": round(ax, 4),
            "accel_y_g": round(ay, 4),
            "accel_z_g": round(az, 4),
            "vibration_rms_g": round(rms + self.base_rms_g, 4),
        }