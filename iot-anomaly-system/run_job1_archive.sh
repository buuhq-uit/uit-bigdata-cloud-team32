#!/usr/bin/env bash
set -euo pipefail

docker compose up -d
sleep 3

docker exec -it spark bash -lc '
  /opt/spark/bin/spark-submit \
    --conf spark.jars.ivy=/opt/spark-app/.ivy2 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
    --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    --conf spark.hadoop.fs.s3a.access.key=minioadmin \
    --conf spark.hadoop.fs.s3a.secret.key=minioadmin123 \
    --conf spark.hadoop.fs.s3a.path.style.access=true \
    --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
    /opt/spark-app/job1_archive_to_minio.py
'
