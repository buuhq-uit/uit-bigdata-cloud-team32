from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.config import APP_NAME
from core.kafka import create_producer, close_producer
from api.routes.health import router as health_router
from api.routes.ingest import router as ingest_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.producer = create_producer()
    try:
        yield
    finally:
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