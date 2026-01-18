from typing import Optional
from fastapi import HTTPException
from .config import API_KEY

def require_api_key(x_api_key: Optional[str]) -> None:
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")