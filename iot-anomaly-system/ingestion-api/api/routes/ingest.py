from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, HTTPException, Request
from core.auth import require_api_key
from core.config import DEFAULT_LOCATION, DEFAULT_MODEL, KAFKA_TOPIC_RAW
from core.time import utc_iso_ts
from core.validation import clamp
from schemas.ingest import IngestPayload

router = APIRouter()

@router.post("/ingest")
def ingest(
    payload: IngestPayload,
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    require_api_key(x_api_key)

    producer = getattr(request.app.state, "producer", None)
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

    if "humidity" in metrics and metrics["humidity"] is not None:
        metrics["humidity"] = clamp(float(metrics["humidity"]), 0.0, 100.0)
    if "soil_moisture" in metrics and metrics["soil_moisture"] is not None:
        metrics["soil_moisture"] = clamp(float(metrics["soil_moisture"]), 0.0, 100.0)

    msg: Dict[str, Any] = {
        "ts": payload.ts or utc_iso_ts(),
        "device_id": payload.device_id,
        "location": payload.location or DEFAULT_LOCATION,
        "model": payload.model or DEFAULT_MODEL,
        "metrics": metrics,
        "source": "ingress-rest-api",
    }

    try:
        producer.send(KAFKA_TOPIC_RAW, key=payload.device_id, value=msg)
        producer.flush(timeout=10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to publish to Kafka: {e}")

    return {
        "status": "sent",
        "topic": KAFKA_TOPIC_RAW,
        "device_id": payload.device_id,
        "location": payload.location or DEFAULT_LOCATION,
         "model": payload.model or DEFAULT_MODEL,
        # "metrics": list(metrics.keys()),
        "metrics": metrics,
    }