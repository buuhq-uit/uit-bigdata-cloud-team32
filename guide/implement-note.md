# iot anamoly system

## Step 1: Create docker-compose.yml file

```shell
docker compose up -d
```

## Step 2: Create topics in Kafka
```shell
docker exec -it kafka sh -lc '
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic iot.sensor.raw --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic iot.sensor.anomaly --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
'
```
### Test produce message:
```shell
docker exec -it kafka sh -lc '
echo "{\"ts\":\"2026-01-13T00:00:00Z\",\"device_id\":\"sim-001\",\"metrics\":{\"temperature\":42.5,\"humidity\":70.0}}" \
| /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic iot.sensor.raw
'
```
### Test consume message:
```shell
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --property print.key=true --property print.value=true
```

## Step 3: Configure MQTT Broker

### Create mosquitto/config/mosquitto.conf

```shell
nano mosquitto/config/mosquitto.conf
```

```text
allow_anonymous false
password_file /mosquitto/config/password.txt

# MQTT TCP listener
listener 1883
protocol mqtt

# WebSocket listener (matches docker-compose port 9001)
listener 9001
protocol websockets
```

Create mosquitto/config/password.txt

```shell
nano mosquitto/config/password.txt
# create username and passworf 
# docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/password.txt <username> <password>
docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/password.txt iot P@sswordMQTT#2025
```

```shell
# Recreate mosquitto with updated config (if changed)
# docker compose -f iot-anomaly-system/docker-compose.yml up -d mosquitto
docker compose up -d mosquitto
```

```shell
## send mqtt test message
docker exec -it mosquitto mosquitto_pub \
  -h mosquitto -p 1883 \
  -u iot -P 'P@sswordMQTT#2025' \
  -t 'iot/esp32-001/telemetry' \
  -m '{"device_id":"esp32-002","temperature":24.2,"humidity":52.1,"soil_moisture":31}'

## receive mqtt test message
docker exec -it mosquitto mosquitto_sub \
  -h mosquitto -p 1883 \
  -u iot -P 'P@sswordMQTT#2025' \
  -t 'iot/#' \
  -v
```

## Step 3: Tao bucket MinIO, postgessql

### MinIO bucket
```text
Vào MinIO Console → Buckets → Create bucket:
bucket name: iot-datalake
```

### Tạo bảng Postgres (devices + anomalies)

```sql
CREATE DATABASE iotdb;
CREATE TABLE IF NOT EXISTS devices (
  device_id TEXT PRIMARY KEY,
  location  TEXT,
  model     TEXT
);

CREATE TABLE IF NOT EXISTS anomalies (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  device_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  value DOUBLE PRECISION,
  score DOUBLE PRECISION,
  method TEXT,
  severity TEXT
);

-- CREATE TABLE IF NOT EXISTS iot_anomalies_window (
--   window_start TIMESTAMPTZ,
--   window_end   TIMESTAMPTZ,
--   device_id    TEXT,
--   temp_mean    DOUBLE PRECISION,
--   temp_std     DOUBLE PRECISION,
--   hum_mean     DOUBLE PRECISION,
--   hum_std      DOUBLE PRECISION,
--   is_anomaly   BOOLEAN
-- );


INSERT INTO devices(device_id, location, model)
VALUES ('sim-001', 'lineA-zone3', 'SIMULATOR')
ON CONFLICT (device_id) DO NOTHING;

select * from devices;
select * from anomalies;
```

## Bước 4 — Tạo Grafana datasources (InfluxDB + Postgres)

```shell
nano grafana/provisioning/datasources/datasources.yml
```

```text
apiVersion: 1

datasources:
  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    jsonData:
      version: Flux
      organization: iot-org
      defaultBucket: iot-bucket
      tlsSkipVerify: true
    secureJsonData:
      token: iot-token-123
    isDefault: true

  - name: PostgreSQL
    type: postgres
    access: proxy
    url: postgresdb:5432
    user: postgres
    secureJsonData:
      password: P@sswordDb#Pi!2025
    jsonData:
      database: iotdb
      sslmode: disable
      postgresVersion: 1600
```


## Step 4: Ingestion Api

```shell
curl http://localhost:6902/health
curl http://10.1.1.10:6902/health
curl https://api.technote.online/health

curl -X POST http://localhost:6902/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: team32-secret" \
  -d '{
    "device_id": "esp32-001",
    "location":"farm-zone-1",
    "model":"ESP32",
    "temperature": 28.2,
    "humidity": 65.0,
    "soil_moisture": 40.5
  }'

  curl -X POST https://api.technote.online/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: team32-secret" \
  -d '{
    "device_id": "esp32-001",
    "location":"farm-zone-1",
    "model":"ESP32",
    "temperature": 28.2,
    "humidity": 65.0,
    "soil_moisture": 40.5
  }'
```

## Step 5: Run 3 spark jobs:

### Job 1:
```shell
## run
./run_job1_archive.sh

## check process
docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job1_archive_to_minio.py' | grep -v grep"

## check logs
docker exec -it spark-jobs bash -lc 'tail -n 500 -f /opt/spark-app/job1.log'
```

### Job 2:
```shell
## run
./run_job1_archive.sh

## check process
docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job2_speed_anomaly_to_influx.py' | grep -v grep"

## check logs
docker exec -it spark-jobs bash -lc 'tail -n 500 -f /opt/spark-app/job2.log'
```

### Job 3:
```shell
## run
./run_job3_batch.sh

## check process
docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job3_batch_offline_analytics.py' | grep -v grep"

## check logs
docker exec -it spark-jobs bash -lc 'tail -n 500 -f /opt/spark-app/job3.log'
```

## Step 6: send data test

```shell
# sudo apt install -y python3-venv python3-pip
sudo apt install python3-full python3-venv

cd ./iot-anomaly-system
python3 -m venv .venv
source .venv/bin/activate

sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
grep kafka /etc/hosts
```
```shell
## send mqtt and rest api
python sim-producer/main.py

## produce to kafka directy
python sim-producer/sim-producer.py
```


## Step 7: Check Data flow

### MQTT and Kafka
```shell
## mqtt
docker exec -it mosquitto mosquitto_sub \
  -h mosquitto -p 1883 \
  -u iot -P 'P@sswordMQTT#2025' \
  -t 'iot/#' \
  -v

## Kafka Consume
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --property print.key=true --property print.value=true
```

### InfluxDb

```shell
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
```

### MinIO
MinIO có raw archive

### Postgressql
```shell
select ts, device_id, metric, value, score, method, severity
from anomalies
order by ts desc
limit 50;
```


## Bước 8 — Tạo dashboard nhanh trong Grafana (Minimum)

Panel 1 – Realtime Sensor Metrics (Line chart) ✅ (bước này)
Panel 2 – Anomaly score / anomaly flag (Realtime)
Panel 3 – Anomaly count theo device (24h) – PostgreSQL


```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
  |> filter(fn: (r) => r._field == "temperature")
  |> filter(fn: (r) => r.device_id == "sim-001")
```

```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
  |> filter(fn: (r) => r._field == "humidity")
  |> filter(fn: (r) => r.device_id == "sim-001")
```

```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
  |> filter(fn: (r) => r._field == "soil_moisture")
  |> filter(fn: (r) => r.device_id == "sim-002")

```

```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_anomalies")
  |> filter(fn: (r) => r._field == "score")
  |> filter(fn: (r) => r.device_id == "sim-002")
```

-- old
Vào Grafana (localhost:3000) → Connections → Data sources:
InfluxDB và PostgreSQL phải “green”.

Panel 1: Temperature (InfluxDB)

Query Flux mẫu:

```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")
  |> filter(fn: (r) => r._field == "temperature")
  |> filter(fn: (r) => r.device_id == "sim-001")
```
Panel 2: Anomaly score (InfluxDB)
```
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_anomalies")
  |> filter(fn: (r) => r._field == "score")
  |> filter(fn: (r) => r.device_id == "sim-001")
```
```text
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_anomalies")
  |> filter(fn: (r) => r._field == "score")
```



Panel 3: Bảng anomalies (PostgreSQL)
Query SQL:
```sql
select ts, device_id, metric, value, score, method, severity
from anomalies
order by ts desc
limit 50;
```


## =====================
```text


# Rebuild API to include paho-mqtt
docker compose -f iot-anomaly-system/docker-compose.yml build ingestion-api
docker compose -f iot-anomaly-system/docker-compose.yml up -d ingestion-api

docker exec -it mosquitto mosquitto_pub \
  -h mosquitto -p 1883 \
  -u iot -P 'P@sswordMQTT#2025' \
  -t 'iot/esp32-001/telemetry' \
  -m '{"device_id":"esp32-002","temperature":24.2,"humidity":52.1,"soil_moisture":31}'

  docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --property print.key=true --property print.value=true
```



## Step 99: prepare python environment
```shell
# sudo apt install -y python3-venv python3-pip
sudo apt install python3-full python3-venv

cd ./iot-anomaly-system
python3 -m venv .venv
source .venv/bin/activate

# install package in requirement
pip install -r requirements.txt

sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
grep kafka /etc/hosts
```

