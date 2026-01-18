from typing import Optional, Dict
from pydantic import BaseModel, Field

class IngestPayload(BaseModel):
    device_id: str = Field(..., examples=["esp32-001", "sim-001"])
    ts: Optional[str] = Field(None)
    location: Optional[str] = None
    model: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None