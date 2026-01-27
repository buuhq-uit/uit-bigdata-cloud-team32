#!/usr/bin/env python3
"""Environment sensors (temperature, humidity, soil moisture)"""
from typing import Dict
from .base import BaseGenerator, DeviceContext, _noise

class TempHumidityGenerator(BaseGenerator):
    """Simulate DHT22-like temperature and humidity sensor"""
    def __init__(self, ctx: DeviceContext, base_temp: float = 24.0, base_hum: float = 55.0):
        super().__init__(ctx)
        self.base_temp = base_temp
        self.base_hum = base_hum
    
    def next_metrics(self) -> Dict[str, float]:
        temp = self.base_temp + _noise(0.7)
        hum = self.base_hum + _noise(2.0)
        hum = max(0.0, min(100.0, hum))
        return {
            "temperature": round(temp, 2),
            "humidity": round(hum, 2),
        }

class SoilMoistureGenerator(BaseGenerator):
    """Simulate soil moisture sensor with temperature"""
    def __init__(self, ctx: DeviceContext, base_soil: float = 35.0, base_temp: float = 23.0):
        super().__init__(ctx)
        self.base_soil = base_soil
        self.base_temp = base_temp
    
    def next_metrics(self) -> Dict[str, float]:
        soil = self.base_soil + _noise(3.0)
        soil = max(0.0, min(100.0, soil))
        temp = self.base_temp + _noise(0.5)
        return {
            "soil_moisture": round(soil, 2),
            "temperature": round(temp, 2),
        }