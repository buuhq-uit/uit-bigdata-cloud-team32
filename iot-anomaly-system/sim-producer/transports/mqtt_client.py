#!/usr/bin/env python3
"""MQTT transport client"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

from generators import DeviceContext

def utc_iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()

class MQTTClient:
    """MQTT client for sending telemetry"""
    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str], base_topic: str):
        self.host = host
        self.port = port
        self.base_topic = base_topic
        self.client = mqtt.Client()
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.connect(host, port, keepalive=30)
        self.client.loop_start()
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected to {self.host}:{self.port}")
        else:
            print(f"[MQTT] Connection failed: rc={rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"[MQTT] Disconnected: rc={rc}")
    
    def send(self, ctx: DeviceContext, metrics: Dict[str, float]) -> None:
        """Send metrics via MQTT"""
        topic = f"{self.base_topic}/{ctx.device_id}/telemetry"
        msg: Dict[str, Any] = {
            "ts": utc_iso_ts(),
            "device_id": ctx.device_id,
            "location": ctx.location,
            "model": ctx.model,
            "metrics": metrics,
        }
        payload = json.dumps(msg)
        try:
            result = self.client.publish(topic, payload, qos=0, retain=False)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] ✓ {ctx.device_id:30s} → {topic} {list(metrics.keys())}")
            else:
                print(f"[MQTT] ✗ {ctx.device_id}: publish failed rc={result.rc}")
        except Exception as e:
            print(f"[MQTT] ✗ {ctx.device_id}: {e}")
    
    def close(self) -> None:
        """Close connection"""
        self.client.loop_stop()
        self.client.disconnect()

def run_mqtt_sim(devices: List[Any], host: str, port: int, username: Optional[str], 
                 password: Optional[str], base_topic: str, interval_sec: float = 1.0) -> None:
    """Run MQTT simulator loop"""
    client = MQTTClient(host, port, username, password, base_topic)
    try:
        print(f"\n[MQTT Simulator] Started with {len(devices)} devices (interval={interval_sec}s)")
        print(f"[MQTT Simulator] Broker: {host}:{port}, Topic: {base_topic}/#")
        print("-" * 80)
        time.sleep(1)  # Wait for connection
        while True:
            for gen in devices:
                metrics = gen.next_metrics()
                client.send(gen.ctx, metrics)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\n[MQTT Simulator] Stopped")
    finally:
        client.close()