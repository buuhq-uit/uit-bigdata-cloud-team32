from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from kafka import KafkaConsumer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_ANOMALY = os.getenv("KAFKA_TOPIC_ANOMALY", "iot.sensor.anomaly")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "anomaly-alert-group")

SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "3.0"))
ONLY_FLAGGED = os.getenv("ONLY_FLAGGED", "true").lower() == "true"


def extract_score_and_flag(event: Dict[str, Any]):
    score = event.get("score")
    is_anomaly = event.get("is_anomaly")

    if score is None and isinstance(event.get("anomaly"), dict):
        score = event["anomaly"].get("score")
        is_anomaly = event["anomaly"].get("is_anomaly")

    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    try:
        flag_i = int(is_anomaly) if is_anomaly is not None else None
    except Exception:
        flag_i = None

    return score_f, flag_i


def should_alert(event: Dict[str, Any]) -> bool:
    score, flag = extract_score_and_flag(event)
    if score is None:
        return False

    if ONLY_FLAGGED and flag is not None:
        return flag == 1

    return abs(score) >= SCORE_THRESHOLD


def format_alert(event: Dict[str, Any]) -> str:
    device_id = event.get("device_id") or event.get("deviceId") or "unknown-device"
    metric = event.get("metric") or (event.get("anomaly") or {}).get("metric") or "unknown-metric"
    score, flag = extract_score_and_flag(event)
    ts = event.get("ts") or event.get("event_ts") or "unknown-ts"

    return f"[ANOMALY ALERT] ts={ts} device_id={device_id} metric={metric} score={score} flag={flag}"


def main():
    print(f"Starting anomaly-alert consumer topic={TOPIC_ANOMALY} bootstrap={KAFKA_BOOTSTRAP}")
    consumer = KafkaConsumer(
        TOPIC_ANOMALY,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    while True:
        try:
            for msg in consumer:
                event = msg.value
                if isinstance(event, dict) and should_alert(event):
                    print(format_alert(event))
        except Exception as e:
            print(f"[ERROR] consumer loop error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
