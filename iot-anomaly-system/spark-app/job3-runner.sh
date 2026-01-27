#!/usr/bin/env bash
set -euo pipefail

# Configurable interval (seconds), default 300
INTERVAL="${JOB3_INTERVAL:-300}"

# Basics
SPARK_SUBMIT=/opt/spark/bin/spark-submit
IVY_DIR=/opt/spark-app/.ivy2
SCRIPT="/opt/spark-app/job3-batch-offline/main.py"

# Ensure shared modules import (common/)
export PYTHONPATH="/opt/spark-app:${PYTHONPATH:-}"

# Only Hadoop AWS + AWS SDK needed for offline S3 parquet
HADOOP_AWS_PKG="org.apache.hadoop:hadoop-aws:3.3.4"
AWS_BUNDLE_PKG="com.amazonaws:aws-java-sdk-bundle:1.12.262"
PACKAGES="${HADOOP_AWS_PKG},${AWS_BUNDLE_PKG}"

# S3 conf args (array-safe)
COMMON_S3_CONF=(
  --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000
  --conf spark.hadoop.fs.s3a.access.key=minioadmin
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin123
  --conf spark.hadoop.fs.s3a.path.style.access=true
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false
)

trap 'echo "[runner] stop signal"; pkill -P $$ || true; exit 0' TERM INT

while true; do
  echo "[runner] starting offline batch run..."
  "$SPARK_SUBMIT" \
    --conf "spark.jars.ivy=$IVY_DIR" \
    --packages "$PACKAGES" \
    "${COMMON_S3_CONF[@]}" \
    "$SCRIPT" || echo "[runner] run failed (exit $?)"
  echo "[runner] sleeping ${INTERVAL}s before next run..."
  sleep "$INTERVAL"
done