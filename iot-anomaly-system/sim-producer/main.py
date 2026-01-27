#!/usr/bin/env python3
"""
IoT Sensor Simulator - Multi-zone Multi-protocol
Simulates sensors from multiple zones using different protocols:
- Zone 1 (Production Floor): REST API
- Zone 2 (Storage Area): MQTT
"""
import argparse
import threading
from typing import List, Any

from config import get_zone1_devices, get_zone2_devices, DeviceConfig
from generators import (
    DeviceContext,
    MachineVibrationGenerator,
    AcousticLevelGenerator,
    MotorStatusGenerator,
    ProcessGaugeGenerator,
    TempHumidityGenerator,
    SoilMoistureGenerator,
)
from transports import run_rest_sim, run_mqtt_sim

# Generator class mapping
GENERATOR_MAP = {
    "MachineVibrationGenerator": MachineVibrationGenerator,
    "AcousticLevelGenerator": AcousticLevelGenerator,
    "MotorStatusGenerator": MotorStatusGenerator,
    "ProcessGaugeGenerator": ProcessGaugeGenerator,
    "TempHumidityGenerator": TempHumidityGenerator,
    "SoilMoistureGenerator": SoilMoistureGenerator,
}

def create_generators(device_configs: List[DeviceConfig]) -> List[Any]:
    """Create generator instances from device configs"""
    generators = []
    for cfg in device_configs:
        ctx = DeviceContext(
            device_id=cfg.device_id,
            location=cfg.location,
            model=cfg.model,
        )
        gen_class = GENERATOR_MAP.get(cfg.generator_class)
        if not gen_class:
            print(f"Warning: Unknown generator class {cfg.generator_class}")
            continue
        gen = gen_class(ctx, **cfg.generator_params)
        generators.append(gen)
    return generators

def print_device_summary():
    """Print device summary table"""
    zone1 = get_zone1_devices()
    zone2 = get_zone2_devices()
    
    print("\n" + "="*80)
    print("DEVICE SIMULATION SUMMARY")
    print("="*80)
    
    print(f"\n📡 Zone 1 - Production Floor (REST API) - {len(zone1)} devices:")
    print("-" * 80)
    for d in zone1:
        print(f"  • {d.device_id:25s} | {d.model:15s} | {d.sensor_type}")
    
    print(f"\n📡 Zone 2 - Storage Area (MQTT) - {len(zone2)} devices:")
    print("-" * 80)
    for d in zone2:
        print(f"  • {d.device_id:25s} | {d.model:15s} | {d.sensor_type}")
    
    print("\n" + "="*80 + "\n")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="IoT Sensor Simulator - Multi-zone Multi-protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run both zones (REST + MQTT)
  python main.py --mode both --interval 1.0
  
  # Run Zone 1 only (REST)
  python main.py --mode zone1 --api-url http://localhost:6902
  
  # Run Zone 2 only (MQTT)
  python main.py --mode zone2 --mqtt-host localhost
        """
    )
    
    parser.add_argument("--mode", choices=["zone1", "zone2", "both"], default="both",
                        help="Simulation mode: zone1 (REST), zone2 (MQTT), or both")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Sensor reading interval in seconds (default: 1.0)")
    
    # REST (Zone 1)
    parser.add_argument("--api-url", default="http://localhost:6902",
                        help="Ingestion API base URL for Zone 1 (default: http://localhost:6902)")
    parser.add_argument("--api-key", default="team32-secret",
                        help="API key for REST authentication (default: team32-secret)")
    
    # MQTT (Zone 2)
    parser.add_argument("--mqtt-host", default="localhost",
                        help="MQTT broker host for Zone 2 (default: localhost)")
    parser.add_argument("--mqtt-port", type=int, default=1883,
                        help="MQTT broker port (default: 1883)")
    parser.add_argument("--mqtt-username", default="iot",
                        help="MQTT username (default: iot)")
    parser.add_argument("--mqtt-password", default="P@sswordMQTT#2025",
                        help="MQTT password")
    parser.add_argument("--mqtt-base-topic", default="iot",
                        help="MQTT base topic (default: iot)")
    
    args = parser.parse_args()
    
    # Print summary
    print_device_summary()
    
    # Create generators
    zone1_gens = create_generators(get_zone1_devices())
    zone2_gens = create_generators(get_zone2_devices())
    
    if args.mode == "zone1":
        # Run Zone 1 only (REST)
        run_rest_sim(zone1_gens, args.api_url, args.api_key, args.interval)
    
    elif args.mode == "zone2":
        # Run Zone 2 only (MQTT)
        run_mqtt_sim(zone2_gens, args.mqtt_host, args.mqtt_port, 
                     args.mqtt_username, args.mqtt_password, 
                     args.mqtt_base_topic, args.interval)
    
    else:
        # Run both zones in parallel threads
        t1 = threading.Thread(
            target=run_rest_sim,
            args=(zone1_gens, args.api_url, args.api_key, args.interval),
            daemon=True,
            name="Zone1-REST"
        )
        t2 = threading.Thread(
            target=run_mqtt_sim,
            args=(zone2_gens, args.mqtt_host, args.mqtt_port, 
                  args.mqtt_username, args.mqtt_password, 
                  args.mqtt_base_topic, args.interval),
            daemon=True,
            name="Zone2-MQTT"
        )
        
        t1.start()
        t2.start()
        
        try:
            t1.join()
            t2.join()
        except KeyboardInterrupt:
            print("\n\n🛑 All simulators stopped")

if __name__ == "__main__":
    main()