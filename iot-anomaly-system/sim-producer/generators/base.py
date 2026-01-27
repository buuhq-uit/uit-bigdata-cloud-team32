#!/usr/bin/env python3
"""Base generator class and utility functions"""
import random
from typing import Dict
from dataclasses import dataclass

@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    location: str
    model: str

def _noise(scale: float) -> float:
    """Generate uniform random noise"""
    return random.uniform(-scale, scale)

def _maybe_spike(val: float, prob: float, factor: float) -> float:
    """Randomly inject anomaly spike"""
    if random.random() < prob:
        return val * factor
    return val

class BaseGenerator:
    """Base class for all sensor generators"""
    def __init__(self, ctx: DeviceContext):
        self.ctx = ctx
    
    def next_metrics(self) -> Dict[str, float]:
        """Generate next set of metrics - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement next_metrics()")