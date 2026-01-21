#!/usr/bin/env bash
set -euo pipefail

BOOTSTRAP="${BOOTSTRAP:-kafka:9092}"
RAW_TOPIC="${RAW_TOPIC:-iot.sensor.raw}"
ANOM_TOPIC="${ANOM_TOPIC:-iot.sensor.anomaly}"
RAW_PARTS="${RAW_PARTS:-3}"
ANOM_PARTS="${ANOM_PARTS:-3}"
REPL="${REPL:-1}"

echo "[topics-init] Waiting for Kafka at ${BOOTSTRAP}..."
for i in $(seq 1 120); do
  if /opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP}" --list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "[topics-init] Creating topics if not exists..."
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP}" --create --if-not-exists --topic "${RAW_TOPIC}"  --partitions "${RAW_PARTS}"  --replication-factor "${REPL}" || true
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP}" --create --if-not-exists --topic "${ANOM_TOPIC}" --partitions "${ANOM_PARTS}" --replication-factor "${REPL}" || true

echo "[topics-init] Current topics:"
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP}" --list || true
echo "[topics-init] Done."