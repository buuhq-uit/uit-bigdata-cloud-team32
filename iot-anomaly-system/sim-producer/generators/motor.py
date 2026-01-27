#!/usr/bin/env python3
"""Motor monitoring generators (current, RPM, temperature)"""
import time
import math
from typing import Dict
from .base import BaseGenerator, DeviceContext, _noise, _maybe_spike

class MotorStatusGenerator(BaseGenerator):
    """Simulate motor monitoring (current, RPM, temperature)"""
    def __init__(self, ctx: DeviceContext, base_current_a: float = 6.0, 
                 base_rpm: float = 1500.0, base_temp_c: float = 60.0):
        super().__init__(ctx)
        self.base_current_a = base_current_a
        self.base_rpm = base_rpm
        self.base_temp_c = base_temp_c
    
    def next_metrics(self) -> Dict[str, float]:
        t = time.time()
        # Motor current with slow drift
        current = self.base_current_a + 0.8 * math.sin(2 * math.pi * 0.5 * t) + _noise(0.3)
        # RPM with very slow oscillation
        rpm = self.base_rpm + 40.0 * math.sin(2 * math.pi * 0.05 * t) + _noise(10.0)
        # Temperature follows current
        temp = self.base_temp_c + (current - self.base_current_a) * 2.0 + _noise(1.0)
        
        # Inject anomalies
        current = _maybe_spike(current, 0.01, 1.8)  # Overload
        rpm = _maybe_spike(rpm, 0.005, 0.6)  # Sudden drop
        temp = _maybe_spike(temp, 0.008, 1.25)  # Overheat
        
        return {
            "motor_current_a": round(current, 3),
            "rpm": round(rpm, 1),
            "temperature_c": round(temp, 2),
        }