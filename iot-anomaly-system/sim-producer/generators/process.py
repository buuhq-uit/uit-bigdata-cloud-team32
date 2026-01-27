#!/usr/bin/env python3
"""Process gauge generators (temperature, pressure, flow)"""
import time
import math
from typing import Dict
from .base import BaseGenerator, DeviceContext, _noise, _maybe_spike

class ProcessGaugeGenerator(BaseGenerator):
    """Simulate process monitoring (temperature, pressure, flow)"""
    def __init__(self, ctx: DeviceContext, base_temp_c: float = 60.0,
                 base_pressure_bar: float = 2.0, base_flow_lpm: float = 20.0):
        super().__init__(ctx)
        self.base_temp_c = base_temp_c
        self.base_pressure_bar = base_pressure_bar
        self.base_flow_lpm = base_flow_lpm
    
    def next_metrics(self) -> Dict[str, float]:
        t = time.time()
        # Temperature with slow cycles
        temp = self.base_temp_c + 1.5 * math.sin(2 * math.pi * 0.1 * t) + _noise(0.5)
        # Pressure correlates with flow
        pressure = self.base_pressure_bar + 0.2 * math.sin(2 * math.pi * 0.07 * t + 0.8) + _noise(0.05)
        flow = self.base_flow_lpm + 2.5 * math.sin(2 * math.pi * 0.12 * t + 0.3) + _noise(0.5)
        
        # Inject anomalies
        temp = _maybe_spike(temp, 0.01, 1.2)
        pressure = _maybe_spike(pressure, 0.008, 1.4)
        flow = _maybe_spike(flow, 0.01, 0.5)  # Flow drop
        
        return {
            "temperature_c": round(temp, 2),
            "pressure_bar": round(pressure, 3),
            "flow_lpm": round(flow, 2),
        }