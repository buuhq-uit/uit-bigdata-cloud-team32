from datetime import datetime, timezone

def utc_iso_ts() -> str:
    return datetime.now(timezone.utc).isoformat()