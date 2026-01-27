#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="/opt/spark-app:${PYTHONPATH:-}"

SPARK_SUBMIT=/opt/spark/bin/spark-submit
IVY_DIR=/opt/spark-app/.ivy2
SCRIPT="/opt/spark-app/job2-speed-anomaly/main.py"

SPARK_VERSION="${SPARK_VERSION:-3.5.7}"
SPARK_SCALA_VERSION="${SPARK_SCALA_VERSION:-2.12}"

KAFKA_PKG="org.apache.spark:spark-sql-kafka-0-10_${SPARK_SCALA_VERSION}:${SPARK_VERSION}"
HADOOP_AWS_PKG="org.apache.hadoop:hadoop-aws:3.3.4"
AWS_BUNDLE_PKG="com.amazonaws:aws-java-sdk-bundle:1.12.262"
POSTGRES_JDBC_PKG="org.postgresql:postgresql:42.7.3"
PACKAGES="${KAFKA_PKG},${HADOOP_AWS_PKG},${AWS_BUNDLE_PKG},${POSTGRES_JDBC_PKG}"

COMMON_S3_CONF=(
  --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000
  --conf spark.hadoop.fs.s3a.access.key=minioadmin
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin123
  --conf spark.hadoop.fs.s3a.path.style.access=true
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false
)

exec "$SPARK_SUBMIT" \
  --conf "spark.jars.ivy=$IVY_DIR" \
  --packages "$PACKAGES" \
  "${COMMON_S3_CONF[@]}" \
  "$SCRIPT"