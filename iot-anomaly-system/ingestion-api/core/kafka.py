import json
from kafka import KafkaProducer
from .config import KAFKA_BOOTSTRAP

def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",
        linger_ms=20,
    )

def close_producer(producer: KafkaProducer) -> None:
    try:
        producer.flush(timeout=10)
    except Exception:
        pass
    producer.close()