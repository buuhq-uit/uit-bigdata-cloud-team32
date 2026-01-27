#!/usr/bin/env python3
"""REST API transport client"""
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timezone
import requests

from generators import DeviceContext

def utc_iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()

class RESTClient:
    """REST API client for sending telemetry"""
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
    
    def send(self, ctx: DeviceContext, metrics: Dict[str, float]) -> None:
        """Send metrics via REST API"""
        url = f"{self.api_url}/ingest"
        payload: Dict[str, Any] = {
            "ts": utc_iso_ts(),
            "device_id": ctx.device_id,
            "location": ctx.location,
            "model": ctx.model,
            "metrics": metrics,
        }
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            resp = self.session.post(url, headers=headers, data=json.dumps(payload), timeout=5)
            resp.raise_for_status()
            print(f"[REST] ✓ {ctx.device_id:30s} → {list(metrics.keys())}")
        except Exception as e:
            print(f"[REST] ✗ {ctx.device_id}: {e}")
    
    def close(self) -> None:
        """Close session"""
        self.session.close()

def run_rest_sim(devices: List[Any], api_url: str, api_key: str, interval_sec: float = 1.0) -> None:
    """Run REST simulator loop"""
    client = RESTClient(api_url, api_key)
    try:
        print(f"\n[REST Simulator] Started with {len(devices)} devices (interval={interval_sec}s)")
        print(f"[REST Simulator] Target: {api_url}")
        print("-" * 80)
        while True:
            for gen in devices:
                metrics = gen.next_metrics()
                client.send(gen.ctx, metrics)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\n[REST Simulator] Stopped")
    finally:
        client.close()