import math
import requests
from typing import List

from config import INFLUX_URL, INFLUX_ORG, INFLUX_BUCKET, INFLUX_TOKEN, INFLUX_PRECISION, MEASUREMENT_METRICS, MEASUREMENT_ANOMS

_http = requests.Session()

def _escape_tag_value(v: str) -> str:
    return str(v).replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")

def _format_field_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}i"
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return ""
        return repr(float(v))
    s = str(v).replace('"', '\\"')
    return f"\"{s}\""

def _to_ns(ts) -> int:
    return int(ts.timestamp() * 1_000_000_000)

def write_lines(lines: List[str]) -> None:
    if not lines:
        return
    url = f"{INFLUX_URL.rstrip('/')}/api/v2/write"
    params = {"org": INFLUX_ORG, "bucket": INFLUX_BUCKET, "precision": INFLUX_PRECISION}
    headers = {"Authorization": f"Token {INFLUX_TOKEN}", "Content-Type": "text/plain; charset=utf-8"}
    payload = "\n".join(lines)
    resp = _http.post(url, params=params, headers=headers, data=payload, timeout=10)
    if resp.status_code >= 300:
        raise RuntimeError(f"Influx write failed: {resp.status_code} {resp.text[:500]}")

def build_metric_lines(metrics_rows) -> List[str]:
    wide = {}
    for r in metrics_rows:
        if r["ts"] is None:
            continue
        ts_ns = _to_ns(r["ts"])
        tags = (
            ("device_id", r["device_id"] or "unknown"),
            ("location", r["location"] or "unknown"),
            ("model", r["model"] or "unknown"),
        )
        k = (ts_ns, tags)
        wide.setdefault(k, {})
        m = r["metric"]
        v = r["value"]
        if m is not None and v is not None:
            wide[k][m] = float(v)

    lines: List[str] = []
    for (ts_ns, tags), fields in wide.items():
        if not fields:
            continue
        tag_str = ",".join([f"{k}={_escape_tag_value(v)}" for k, v in tags])
        field_parts = []
        for fk, fv in fields.items():
            fv_s = _format_field_value(fv)
            if fv_s != "":
                field_parts.append(f"{_escape_tag_value(fk)}={fv_s}")
        if field_parts:
            lines.append(f"{MEASUREMENT_METRICS},{tag_str} {','.join(field_parts)} {ts_ns}")
    return lines

def build_anom_lines(anom_rows) -> List[str]:
    lines: List[str] = []
    for r in anom_rows:
        if r["ts"] is None:
            continue
        ts_ns = _to_ns(r["ts"])
        tags = [
            ("device_id", r["device_id"] or "unknown"),
            ("location", r["location"] or "unknown"),
            ("model", r["model"] or "unknown"),
            ("metric", r["metric"] or "unknown"),
            ("severity", r["severity"] or "unknown"),
        ]
        tag_str = ",".join([f"{k}={_escape_tag_value(v)}" for k, v in tags])
        v_s = _format_field_value(float(r["value"]) if r["value"] is not None else None)
        s_s = _format_field_value(float(r["score"]) if r["score"] is not None else None)
        field_parts = []
        if v_s != "":
            field_parts.append(f"value={v_s}")
        if s_s != "":
            field_parts.append(f"score={s_s}")
        if field_parts:
            lines.append(f"{MEASUREMENT_ANOMS},{tag_str} {','.join(field_parts)} {ts_ns}")
    return lines