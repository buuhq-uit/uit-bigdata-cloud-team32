#!/usr/bin/env python3
import argparse
import json
import os
import time
import datetime
from kafka import KafkaConsumer

def main():
    parser = argparse.ArgumentParser(description="Check messages on a Kafka topic")
    parser.add_argument("--bootstrap", default=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                        help="Kafka bootstrap servers, e.g. localhost:9092 or kafka:9092")
    parser.add_argument("--topic", default=os.getenv("KAFKA_TOPIC", "iot.sensor.raw"),
                        help="Kafka topic to read")
    parser.add_argument("--max-messages", type=int, default=5,
                        help="Stop after N messages (<=0 to read until timeout)")
    parser.add_argument("--timeout-ms", type=int, default=10000,
                        help="Consumer timeout in ms (no new messages → exit)")
    parser.add_argument("--from-beginning", action="store_true",
                        help="Read from earliest offsets instead of latest")
    args = parser.parse_args()

    group_id = f"check-{int(time.time())}"
    offset_reset = "earliest" if args.from_beginning else "latest"

    consumer = KafkaConsumer(
        args.topic,
        bootstrap_servers=args.bootstrap,
        group_id=group_id,
        auto_offset_reset=offset_reset,
        enable_auto_commit=False,
        consumer_timeout_ms=args.timeout_ms,
        value_deserializer=lambda v: v,   # raw bytes; decode below
        key_deserializer=lambda k: k,
    )

    count = 0
    try:
        for msg in consumer:
            # Decode key/value
            key = msg.key.decode("utf-8") if msg.key else None
            try:
                value = json.loads(msg.value.decode("utf-8"))
            except Exception:
                value = msg.value.decode("utf-8", errors="replace")

            ts_iso = datetime.datetime.fromtimestamp(
                msg.timestamp / 1000.0, tz=datetime.timezone.utc
            ).isoformat()

            print(json.dumps({
                "partition": msg.partition,
                "offset": msg.offset,
                "key": key,
                "kafka_ts": ts_iso,
                "value": value
            }, ensure_ascii=False))

            count += 1
            if args.max_messages > 0 and count >= args.max_messages:
                break
    finally:
        consumer.close()

if __name__ == "__main__":
    main()