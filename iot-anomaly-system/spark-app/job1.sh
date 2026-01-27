#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-start}"

ROOT="/opt/spark-app"
LOG_DIR="$ROOT/logs"
PID_DIR="$ROOT/logs/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

NAME="job1-archive-minio"            # change per file: job2-speed-anomaly, job3-batch-offline
RUNNER="$ROOT/job1-runner.sh"        # change per file: job2-runner.sh, job3-runner.sh
LOG_FILE="$LOG_DIR/job1.log"         # change per file: job2.log, job3.log
PID_FILE="$PID_DIR/job1.pid"         # change per file: job2.pid, job3.pid

start() {
  export PYTHONPATH="/opt/spark-app:${PYTHONPATH:-}"
  touch "$LOG_FILE"

  # Robust PID check: only treat as running if command matches our runner or spark-submit to our job script
  if [[ -f "$PID_FILE" ]]; then
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      cmd="$(ps -p "$pid" -o cmd= || true)"
      if [[ "$cmd" == *"$RUNNER"* ]] || [[ "$cmd" == *spark-submit* ]] && [[ "$cmd" == *"/job1-archive-minio/main.py"* ]]; then
        echo "[start] $NAME already running (pid $pid)"
        return
      else
        echo "[start] removing stale/unrelated pid $pid (cmd: $cmd)"
        rm -f "$PID_FILE"
      fi
    else
      echo "[start] removing stale pid $pid"
      rm -f "$PID_FILE"
    fi
  fi

  echo "[start] $NAME ..."
  nohup /bin/bash "$RUNNER" >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "[start] $NAME started (pid $(cat "$PID_FILE")), log=$LOG_FILE"
}

stop() {
  if [[ -f "$PID_FILE" ]]; then
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "[stop] $NAME (pid $pid) ..."
      # Try graceful stop, then force; also kill children (useful for job3 loop)
      kill -TERM "$pid" || true
      sleep 2
      pkill -P "$pid" || true
      if kill -0 "$pid" 2>/dev/null; then
        echo "[stop] $NAME still running, force kill"
        kill -KILL "$pid" || true
      fi
    else
      echo "[stop] $NAME not running"
    fi
  else
    echo "[stop] $NAME not running"
  fi
  rm -f "$PID_FILE"
}

status() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "[status] $NAME running (pid $(cat "$PID_FILE"))"
  else
    echo "[status] $NAME stopped"
  fi
}

tail_logs() {
  tail -n 200 -f "$LOG_FILE"
}

case "$ACTION" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  tail) tail_logs ;;
  *) echo "Usage: $0 {start|stop|status|tail}"; exit 1 ;;
esac