from fastapi import APIRouter
from core.config import APP_NAME

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}