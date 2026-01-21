#!/usr/bin/env python3
import argparse
import threading

from sim_rest import run_rest_sim
from sim_mqtt import run_mqtt_sim

def main() -> None:
    parser = argparse.ArgumentParser(description="Run REST/MQTT simulators")
    parser.add_argument("--mode", choices=["rest", "mqtt", "both"], default="both")
    parser.add_argument("--interval", type=float, default=1.0)
    # REST
    parser.add_argument("--api-url", default="http://localhost:6902")
    parser.add_argument("--api-key", default="team32-secret")
    # MQTT
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--mqtt-username", default="iot")
    parser.add_argument("--mqtt-password", default="P@sswordMQTT#2025")
    parser.add_argument("--mqtt-base-topic", default="iot")
    args = parser.parse_args()

    if args.mode == "rest":
        run_rest_sim(args.api_url, args.api_key, args.interval)
    elif args.mode == "mqtt":
        run_mqtt_sim(args.mqtt_host, args.mqtt_port, args.mqtt_username, args.mqtt_password, args.mqtt_base_topic, args.interval)
    else:
        t1 = threading.Thread(target=run_rest_sim, args=(args.api_url, args.api_key, args.interval), daemon=True)
        t2 = threading.Thread(target=run_mqtt_sim, args=(args.mqtt_host, args.mqtt_port, args.mqtt_username, args.mqtt_password, args.mqtt_base_topic, args.interval), daemon=True)
        t1.start(); t2.start()
        try:
            t1.join(); t2.join()
        except KeyboardInterrupt:
            print("\nBoth simulators stopped")

if __name__ == "__main__":
    main()