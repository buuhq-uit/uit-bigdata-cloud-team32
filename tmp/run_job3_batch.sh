#!/usr/bin/env bash
set -euo pipefail
echo "==> Start Job3 ...."
# docker compose up -d
sleep 3

docker exec -d spark-jobs bash -lc '
  while true; do
    echo "[job-runner] Run Job3 (Batch Offline Analytics MinIO -> offline_stats)..."
    /opt/spark/bin/spark-submit \
      --conf spark.jars.ivy=/opt/spark-app/.ivy2 \
      --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
      --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
      --conf spark.hadoop.fs.s3a.access.key=minioadmin \
      --conf spark.hadoop.fs.s3a.secret.key=minioadmin123 \
      --conf spark.hadoop.fs.s3a.path.style.access=true \
      --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
      /opt/spark-app/job3_batch_offline_analytics.py \
      > /opt/spark-app/job3.log 2>&1 || true
    sleep 900
  done
  &
'

echo "==>  Job3 started completely in background."
# docker exec -it spark-jobs bash -lc 'tail -n 500 -f /opt/spark-app/job3.log'

