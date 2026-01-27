#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-start}"

ROOT="/opt/spark-app"
JOB1="$ROOT/job1.sh"
JOB2="$ROOT/job2.sh"
JOB3="$ROOT/job3.sh"
LOG_DIR="$ROOT/logs"

case "$ACTION" in
  start)
    bash "$JOB1" start
    bash "$JOB2" start
    bash "$JOB3" start
    ;;
  stop)
    bash "$JOB1" stop
    bash "$JOB2" stop
    bash "$JOB3" stop
    ;;
  status)
    bash "$JOB1" status
    bash "$JOB2" status
    bash "$JOB3" status
    ;;
  tail)
    tail -n 200 -f "$LOG_DIR/job1.log" "$LOG_DIR/job2.log" "$LOG_DIR/job3.log"
    ;;
  *)
    echo "Usage: $0 {start|stop|status|tail}"
    exit 1
    ;;
esac