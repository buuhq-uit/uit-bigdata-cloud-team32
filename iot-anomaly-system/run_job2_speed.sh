#!/usr/bin/env bash
set -euo pipefail

echo "==> Start Job2 compose"
# docker compose up -d

echo "==> Wait a bit for Kafka/Postgres/Influx to be ready (optional)"
sleep 5

# echo "==> Copy streaming job into spark container"
# docker cp ./streaming_job_fixed.py spark:/opt/spark-app/streaming_job.py

# echo "==> (Optional) check topic exists / list topics"
# docker exec -it kafka bash -lc "kafka-topics --bootstrap-server kafka:9092 --list || true"

# echo "==> Run producer in background (if you have it inside container: spark)"
# Nếu producer.py nằm trong /opt/spark-app rồi thì chạy:
# docker exec -d spark bash -lc "python /opt/spark-app/producer.py"

# echo "==> Delete previous checkpoint (if any)"
docker exec -d spark-jobs sh -lc 'rm -rf /tmp/spark-checkpoints/iot_anomaly_v2'

echo "==> Run Spark Streaming job (foreground, Ctrl+C to stop)"
docker exec -d spark-jobs bash -lc '
export PYTHONPATH=/opt/spark-app/.python:$PYTHONPATH

# Kafka
export KAFKA_BOOTSTRAP="kafka:9092"
export KAFKA_TOPIC="iot.sensor.raw"
export KAFKA_STARTING_OFFSETS="earliest"

# Window (demo nhanh)
export WINDOW_DURATION="10 seconds"
export WATERMARK_DELAY="20 seconds"
# export Z_THRESHOLD="3.0"
export MIN_STD="0.05"

# Anomaly detection test
export Z_THRESHOLD="1.5"


# Postgres
export WRITE_TO_POSTGRES=true
export PG_URL="jdbc:postgresql://postgres:5432/iotdb"
export PG_USER="postgres"
export PG_PASSWORD="P@sswordDb#Pi!2025"
export PG_TABLE="anomalies"

# InfluxDB
export WRITE_TO_INFLUX=true
export INFLUX_URL="http://influxdb:8086"
export INFLUX_ORG="iot-org"
export INFLUX_BUCKET="iot-bucket"
export INFLUX_TOKEN="iot-token-123"
export INFLUX_PRECISION="ns"

# Checkpoint
export CHECKPOINT_DIR="/tmp/spark-checkpoints/iot_anomaly_v2"

 /opt/spark/bin/spark-submit \
   --conf spark.jars.ivy=/opt/spark-app/.ivy2 \
   --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
   --jars /opt/spark-app/postgresql.jar \
   /opt/spark-app/job2_speed_anomaly_to_influx.py \
   > /opt/spark-app/job2.log 2>&1 &
'

# docker exec -it spark-jobs bash -lc 'tail -n 200 -f /opt/spark-app/job2.log'

# docker exec -it spark-jobs bash -lc "ps aux | grep -F 'job2_speed_anomaly_to_influx.py' | grep -v grep"