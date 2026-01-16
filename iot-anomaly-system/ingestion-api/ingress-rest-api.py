from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from kafka import KafkaProducer

APP_NAME = "iot-ingestion-api"

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "iot.sensor.raw")

DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "farm-zone-1")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "ESP32")

# ✅ Simple API Key Auth
API_KEY = os.getenv("API_KEY", "team32-secret")  # set in docker-compose for real use
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

producer: KafkaProducer | None = None
app = FastAPI(title=APP_NAME)


def utc_iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_api_key(x_api_key: Optional[str]) -> None:
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


class IngestPayload(BaseModel):
    device_id: str = Field(..., examples=["esp32-001"])
    ts: Optional[str] = None
    location: Optional[str] = None
    model: Optional[str] = None

    metrics: Optional[Dict[str, float]] = None

    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None


@app.on_event("startup")
def startup():
    global producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",
        linger_ms=20,
    )


@app.on_event("shutdown")
def shutdown():
    global producer
    if producer:
        producer.flush()
        producer.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}


@app.post("/ingest")
def ingest(
    payload: IngestPayload,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),  # ✅ header auth
):
    require_api_key(x_api_key)

    global producer
    if not producer:
        raise HTTPException(status_code=500, detail="Kafka producer not ready")

    metrics: Dict[str, float] = {}
    if payload.metrics:
        metrics.update(payload.metrics)

    if payload.temperature is not None:
        metrics["temperature"] = float(payload.temperature)
    if payload.humidity is not None:
        metrics["humidity"] = float(payload.humidity)
    if payload.soil_moisture is not None:
        metrics["soil_moisture"] = float(payload.soil_moisture)

    if not metrics:
        raise HTTPException(status_code=400, detail="No metrics provided")

    msg: Dict[str, Any] = {
        "ts": payload.ts or utc_iso_ts(),
        "device_id": payload.device_id,
        "location": payload.location or DEFAULT_LOCATION,
        "model": payload.model or DEFAULT_MODEL,
        "metrics": metrics,
    }

    producer.send(TOPIC_RAW, key=payload.device_id, value=msg)
    producer.flush()

    return {"status": "sent", "topic": TOPIC_RAW, "device_id": payload.device_id, "metrics": list(metrics.keys())}
