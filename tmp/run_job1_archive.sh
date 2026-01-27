#!/usr/bin/env bash
set -euo pipefail

echo "==> Start Job1 ...."

# docker compose up -d
echo "==> Wait a bit for Kafka/Postgres/Influx to be ready (optional)"
sleep 5


docker exec -d spark-jobs bash -lc '
  /opt/spark/bin/spark-submit \
    --conf spark.jars.ivy=/opt/spark-app/.ivy2 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
    --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    --conf spark.hadoop.fs.s3a.access.key=minioadmin \
    --conf spark.hadoop.fs.s3a.secret.key=minioadmin123 \
    --conf spark.hadoop.fs.s3a.path.style.access=true \
    --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
    /opt/spark-app/job1_archive_to_minio.py \
    > /opt/spark-app/job1.log 2>&1 &
'

echo "==>  Job1 started completely in background."
# docker exec -it spark-jobs bash -lc 'tail -n 500 -f /opt/spark-app/job1.log'