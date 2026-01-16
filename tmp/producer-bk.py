import json, time, random, datetime
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC = "iot.sensor.raw"
DEVICE_ID = "sim-001"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

base_temp = 46.0
base_hum = 70.0

while True:
    # ts = datetime.datetime.utcnow().isoformat() + "Z"
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # normal noise
    temp = base_temp + random.uniform(-0.5, 0.5)
    hum = base_hum + random.uniform(-1.5, 1.5)

    # inject anomaly occasionally
    if random.random() < 0.05:
        temp += random.uniform(8, 15)

    msg = {
        "ts": ts,
        "device_id": DEVICE_ID,
        "location": "lineA-zone3",
        "model": "SIMULATOR",
        "metrics": {
            "temperature": round(temp, 2),
            "humidity": round(hum, 2)
        }
    }

    producer.send(TOPIC, key=DEVICE_ID, value=msg)
    producer.flush()
    print("sent", msg)
    time.sleep(1)
