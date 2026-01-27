#!/usr/bin/env python3
"""Acoustic/microphone signal generators"""
import time
import math
from typing import Dict
from .base import BaseGenerator, DeviceContext, _noise, _maybe_spike

class AcousticLevelGenerator(BaseGenerator):
    """Simulate acoustic sensor (sound level in dB)"""
    def __init__(self, ctx: DeviceContext, base_db: float = 70.0):
        super().__init__(ctx)
        self.base_db = base_db
    
    def next_metrics(self) -> Dict[str, float]:
        t = time.time()
        # Slow oscillation + noise
        db = self.base_db + 5.0 * math.sin(2 * math.pi * 0.2 * t) + _noise(2.0)
        # Inject anomaly: loud spike
        db = _maybe_spike(db, 0.02, 1.3)
        return {"sound_db": round(db, 2)}