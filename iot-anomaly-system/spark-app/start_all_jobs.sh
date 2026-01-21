#!/usr/bin/env bash
set -euo pipefail

echo "[job-runner] Waiting for Kafka & MinIO..."
until (echo > /dev/tcp/kafka/9092) >/dev/null 2>&1; do sleep 2; done
until (echo > /dev/tcp/minio/9000) >/dev/null 2>&1; do sleep 2; done
echo "[job-runner] Dependencies ready."

SPARK_SUBMIT=/opt/spark/bin/spark-submit
IVY_DIR=/opt/spark-app/.ivy2

COMMON_PACKAGES="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262"

COMMON_S3_CONF=(
  --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000
  --conf spark.hadoop.fs.s3a.access.key=minioadmin
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin123
  --conf spark.hadoop.fs.s3a.path.style.access=true
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false
)

echo "[job-runner] Start Job1 (Archive Kafka -> MinIO)..."
$SPARK_SUBMIT \
  --conf spark.jars.ivy=$IVY_DIR \
  --packages $COMMON_PACKAGES \
  "${COMMON_S3_CONF[@]}" \
  /opt/spark-app/job1_archive_to_minio.py \
  &

JOB1_PID=$!

echo "[job-runner] Start Job2 (Speed Kafka -> Influx/Postgres + anomaly)..."
$SPARK_SUBMIT \
  --conf spark.jars.ivy=$IVY_DIR \
  --packages $COMMON_PACKAGES \
  "${COMMON_S3_CONF[@]}" \
  /opt/spark-app/job2_speed_anomaly_to_influx.py \
  &

JOB2_PID=$!

# Job3 chạy theo lịch (ví dụ mỗi 30 phút)
echo "[job-runner] Start Job3 scheduler (every 30 minutes)..."
(
  while true; do
    echo "[job-runner] Run Job3 (Batch Offline Analytics MinIO -> offline_stats)..."
    $SPARK_SUBMIT \
      --conf spark.jars.ivy=$IVY_DIR \
      --packages "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262" \
      "${COMMON_S3_CONF[@]}" \
      /opt/spark-app/job3_batch_offline_analytics.py || true
    sleep 1800
  done
) &

JOB3_PID=$!

# Handle stop
trap "echo '[job-runner] stopping...'; kill -TERM $JOB1_PID $JOB2_PID $JOB3_PID 2>/dev/null || true; wait" SIGINT SIGTERM

# wait
# exit when any child exits non-zero, then kill the rest
while true; do
  if ! wait -n; then
    echo "[job-runner] A job crashed, stopping others..."
    kill -TERM $JOB1_PID $JOB2_PID $JOB3_PID 2>/dev/null || true
    wait
    exit 1
  fi
done