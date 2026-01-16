# iot-bigdata-anomaly

# Bước 0 — Chuẩn bị môi trường trong WSL (Ubuntu)

```shell
mkdir -p ./iot-bigdata-anomaly && cd ./iot-bigdata-anomaly
mkdir -p spark-app producer grafana/provisioning/datasources grafana/provisioning/dashboards grafana/dashboards
```

# Bước 1 — Tạo docker-compose.yml (Kafka + Spark + InfluxDB + Postgres + Grafana + MinIO)

```shell
nano docker-compose.yml
```

```shell
docker compose up -d
docker ps
```

```text
Mở UI:

Grafana: http://localhost:3000
 (admin/admin)

InfluxDB: http://localhost:8086
 (admin/admin12345)

MinIO Console: http://localhost:9001
 (minioadmin/minioadmin123)
```

## Bước 2 — Tạo bucket MinIO cho “Data Lake”

```text
Vào MinIO Console → Buckets → Create bucket:
bucket name: iot-datalake
```

## Bước 3 — Tạo bảng Postgres (devices + anomalies)

```sql
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

```shell
docker restart grafana
```

## Bước 5 — Tạo topics Kafka (raw + anomaly): ok

```shell
docker exec -it kafka sh -lc '
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic iot.sensor.raw --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic iot.sensor.anomaly --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
'
```

### Test produce 1 message:

```shell
docker exec -it kafka sh -lc '
echo "{\"ts\":\"2026-01-13T00:00:00Z\",\"device_id\":\"sim-001\",\"metrics\":{\"temperature\":42.5,\"humidity\":70.0}}" \
| /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic iot.sensor.raw
'
```

### Test consume 1 message:

```shell
docker exec -it kafka sh -lc '
/opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic iot.sensor.raw --from-beginning --max-messages 1
'
```

## Bước 6 — Chạy producer giả lập gửi sensor data vào Kafka

```shell
sudo sh -c 'echo "127.0.0.1 kafka" >> /etc/hosts'
grep kafka /etc/hosts

```

```shell
sudo apt install -y python3-venv python3-pip

python3 -m venv .venv
source .venv/bin/activate
pip install kafka-python
```

```shell
python producer/producer.py
```

### test test consume:

```shell
docker exec -it kafka sh -lc '
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic iot.sensor.raw \
  --from-beginning \
  --max-messages 5
'
```


## Bước 7 — Spark Streaming đọc Kafka, tính anomaly (Z-score), ghi Influx + Postgres + MinIO

### 7.1 Tạo thư mục và phân quyền trên WSL (host)
```shell
cd ~/iot-anomaly

# đảm bảo có folder
mkdir -p spark-app/checkpoints
mkdir -p spark-app/.pip
mkdir -p spark-app/.python

# cấp quyền rộng cho demo (đơn giản, dễ chạy)
chmod -R 777 spark-app
```

### 7.2 Cài requests vào thư mục mount (không dùng --user)

```shell
docker exec -it spark sh -lc "
python3 -m pip install --no-cache-dir --target /opt/spark-app/.python requests
ls -la /opt/spark-app/.python | head
"
```

### 7.3 Tải PostgreSQL JDBC jar vào thư mục mount

```shell
docker exec -it spark sh -lc "
cd /opt/spark-app &&
curl -L -o postgresql.jar https://jdbc.postgresql.org/download/postgresql-42.7.4.jar &&
ls -la postgresql.jar
"
```

## 7.4 Tạo Spark job (Python) — bản Minimum (dùng requests)

```shell
cd ./iot-bigdata-anomaly
nano spark-app/streaming_job_v2.py

```

## 7.5 Script run

```shell
cd ./iot-bigdata-anomaly
nano run_spark_streaming.sh
```

### 7.6 Chạy Spark job với PYTHONPATH trỏ tới thư viện đã cài trong mount

Kiểm tra PATH và tìm spark-submit
```shell
docker exec -it spark sh -lc 'echo $PATH; which spark-submit || true; find / -maxdepth 4 -name spark-submit 2>/dev/null | head -n 20'

```

```shell
cd ./iot-bigdata-anomaly
mkdir -p spark-app/.ivy2 spark-app/.m2
chmod -R 777 spark-app/.ivy2 spark-app/.m2

```

```shell
cd ./iot-bigdata-anomaly
./run_spark_streaming.sh
```


### produce test anomoly

```shell
docker exec -it kafka sh -lc '
/opt/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic iot.sensor.raw <<EOF
{"ts":"2026-01-13T11:42:30Z","device_id":"sim-001","location":"lineA-zone3","model":"SIMULATOR","metrics":{"temperature":45.0,"humidity":70.0}}
{"ts":"2026-01-13T11:42:31Z","device_id":"sim-001","location":"lineA-zone3","model":"SIMULATOR","metrics":{"temperature":46.0,"humidity":70.0}}
{"ts":"2026-01-13T11:42:32Z","device_id":"sim-001","location":"lineA-zone3","model":"SIMULATOR","metrics":{"temperature":47.0,"humidity":70.0}}
EOF
'
```


Chạy spark-submit bằng full path
```shell
docker exec -it spark sh -lc "
export PYTHONPATH=/opt/spark-app/.python:\$PYTHONPATH
/opt/spark/bin/spark-submit \
  --conf spark.jars.ivy=/opt/spark-app/.ivy2 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  --jars /opt/spark-app/postgresql.jar \
  /opt/spark-app/streaming_job.py
"
```

## Bước 8 — Kiểm tra dữ liệu đã chảy

### 8.1 Kiểm tra Postgres có anomalies

```shell
docker exec -it postgres psql -U iot -d iotdb -c "select * from anomalies order by ts desc limit 10;"
```

## 8.2 Kiểm tra MinIO có file raw

Vào MinIO Console → bucket iot-datalake → folder raw/ sẽ thấy json files.

### 8.3 Kiểm tra InfluxDB có measurement
Vào InfluxDB UI → Data Explorer (Flux) thử query:

```shell
from(bucket: "iot-bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "sensor_metrics")

```


## Bước 9 — Tạo dashboard nhanh trong Grafana (Minimum)

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

## Khi nào coi là “xong Minimum”?

Bạn đạt Minimum khi demo được:

Producer gửi data → Kafka
Spark Streaming đọc Kafka và phát hiện anomaly (nổ điểm bất thường)

Grafana thấy:
line chart temperature
anomaly score/points
bảng anomalies từ Postgres

MinIO có raw archive