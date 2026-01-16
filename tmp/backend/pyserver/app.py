from flask import Flask, jsonify
from kafka import KafkaProducer
import time, json

app = Flask(__name__)
producer = None

def get_producer():
    global producer
    while producer is None:
        try:
            print("Connecting to Kafka...")
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Kafka connected")
        except Exception as e:
            print("Kafka not ready:", e)
            time.sleep(5)
    return producer

@app.route('/favicon.ico')
def favicon():
    return '', 204

# ===== RECEIVE SENSOR + 2 DEVICE STATE =====
@app.route('/<temperature>/<humidity>/<soil>/<device1>/<device2>')
def receive_data(temperature, humidity, soil, device1, device2):
    p = get_producer()

    payload = {
        "type": "iot_event",
        "temperature": float(temperature),
        "humidity": float(humidity),
        "soil_moisture": int(soil),

        "device1": {
            "name": "pump",
            "state": "ON" if device1 == "1" else "OFF"
        },
        "device2": {
            "name": "fan",
            "state": "ON" if device2 == "1" else "OFF"
        },

        "timestamp": time.time()
    }

    p.send('my_topic', payload)
    p.flush()

    print("Kafka event:", payload)

    return jsonify(payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
