#!/usr/bin/env python3
"""
Device Registry and Zone Configuration
Defines all simulated devices grouped by zone and communication protocol
"""
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass(frozen=True)
class DeviceConfig:
    device_id: str
    model: str
    location: str
    sensor_type: str
    generator_class: str
    generator_params: Dict[str, Any]

# Zone 1 - Production Floor (REST API)
ZONE1_DEVICES: List[DeviceConfig] = [
    DeviceConfig(
        device_id="zone1-motor-001",
        model="Motor-A",
        location="zone1-production-floor",
        sensor_type="motor_monitoring",
        generator_class="MotorStatusGenerator",
        generator_params={"base_current_a": 6.0, "base_rpm": 1500.0, "base_temp_c": 60.0}
    ),
    DeviceConfig(
        device_id="zone1-pump-001",
        model="Pump-B",
        location="zone1-production-floor",
        sensor_type="process_gauge",
        generator_class="ProcessGaugeGenerator",
        generator_params={"base_temp_c": 55.0, "base_pressure_bar": 2.0, "base_flow_lpm": 20.0}
    ),
    DeviceConfig(
        device_id="zone1-vibsensor-001",
        model="VibSense-X",
        location="zone1-production-floor",
        sensor_type="vibration_monitor",
        generator_class="MachineVibrationGenerator",
        generator_params={"base_rms_g": 0.2}
    ),
    DeviceConfig(
        device_id="zone1-acoustic-001",
        model="MicArray-Z",
        location="zone1-production-floor",
        sensor_type="acoustic_monitor",
        generator_class="AcousticLevelGenerator",
        generator_params={"base_db": 70.0}
    ),
]

# Zone 2 - Storage Area (MQTT)
ZONE2_DEVICES: List[DeviceConfig] = [
    DeviceConfig(
        device_id="zone2-temp-001",
        model="ESP32-DHT22",
        location="zone2-storage-area",
        sensor_type="environment",
        generator_class="TempHumidityGenerator",
        generator_params={"base_temp": 24.0, "base_hum": 55.0}
    ),
    DeviceConfig(
        device_id="zone2-temp-002",
        model="ESP32-DHT22",
        location="zone2-storage-area",
        sensor_type="environment",
        generator_class="TempHumidityGenerator",
        generator_params={"base_temp": 22.0, "base_hum": 60.0}
    ),
    DeviceConfig(
        device_id="zone2-soil-001",
        model="ESP32-Soil",
        location="zone2-storage-area",
        sensor_type="soil_monitor",
        generator_class="SoilMoistureGenerator",
        generator_params={"base_soil": 35.0, "base_temp": 23.0}
    ),
    DeviceConfig(
        device_id="zone2-hvac-001",
        model="HVAC-Monitor",
        location="zone2-storage-area",
        sensor_type="climate_control",
        generator_class="ProcessGaugeGenerator",
        generator_params={"base_temp_c": 18.0, "base_pressure_bar": 1.5, "base_flow_lpm": 15.0}
    ),
]

def get_zone1_devices() -> List[DeviceConfig]:
    """Get Zone 1 devices (REST)"""
    return ZONE1_DEVICES

def get_zone2_devices() -> List[DeviceConfig]:
    """Get Zone 2 devices (MQTT)"""
    return ZONE2_DEVICES

def get_all_devices() -> Dict[str, List[DeviceConfig]]:
    """Get all devices grouped by zone"""
    return {
        "zone1": ZONE1_DEVICES,
        "zone2": ZONE2_DEVICES,
    }