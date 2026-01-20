from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.config import APP_NAME
from core.kafka import create_producer, close_producer
from api.routes.health import router as health_router
from api.routes.ingest import router as ingest_router

# new: mqtt bridge imports/config
from mqtt.mqtt_bridge import MQTTBridge
from core.config import (
    MQTT_ENABLE, MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPIC
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.producer = create_producer()
    # start MQTT bridge if enabled
    app.state.mqtt_bridge = None
    if MQTT_ENABLE:
        bridge = MQTTBridge(
            app=app,
            host=MQTT_HOST,
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            topic=MQTT_TOPIC,
        )
        bridge.start()
        app.state.mqtt_bridge = bridge
        
    try:
        yield
    finally:
        # stop MQTT bridge
        bridge = getattr(app.state, "mqtt_bridge", None)
        if bridge:
            bridge.stop()
        # close Kafka
        producer = getattr(app.state, "producer", None)
        if producer:
            close_producer(producer)

def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(ingest_router)
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)