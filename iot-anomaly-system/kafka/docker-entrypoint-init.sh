#!/usr/bin/env bash
set -euo pipefail

# Forward signals to broker
trap 'kill -TERM $BROKER_PID 2>/dev/null || true' SIGINT SIGTERM

# Start Kafka using base CMD (passed as "$@") in background
"$@" &
BROKER_PID=$!

# Wait until topics API responds
for i in $(seq 1 120); do
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1 && break
  sleep 2
done

/usr/local/bin/topics-init.sh || true

# Keep container tied to broker process
wait "$BROKER_PID"