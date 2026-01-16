# /opt/spark-app/streaming_job.py
"""
IoT Anomaly Detection (Spark Structured Streaming + Kafka)
- Read JSON events from Kafka topic iot.sensor.raw
- Explode metrics map -> (device_id, metric, value, ts, ...)
- Compute per-device+metric rolling stats over a time window (mean/stddev) and z-score
- Write:
  1) InfluxDB 2.x (HTTP line protocol via requests):
     - sensor_metrics measurement: fields temperature, humidity, ... (wide rows)
     - sensor_anomalies measurement: fields score, value; tag metric
  2) PostgreSQL via JDBC: anomalies table (event-level anomalies only)

This file is designed to match your implement.md dashboards:
- Influx measurement: sensor_metrics
  fields: temperature, humidity
  tags: device_id, location, model
- Influx measurement: sensor_anomalies
  fields: score, value
  tags: device_id, metric, location, model

Env vars (with defaults):
- KAFKA_BOOTSTRAP=kafka:9092
- KAFKA_TOPIC=iot.sensor.raw
- KAFKA_STARTING_OFFSETS=latest|earliest
- WINDOW_DURATION="1 minute" (demo: "10 seconds")
- WATERMARK_DELAY="2 minutes" (demo: "20 seconds")
- Z_THRESHOLD=3.0
- MIN_STD=0.05

Postgres:
- WRITE_TO_POSTGRES=true|false
- PG_URL=jdbc:postgresql://postgres:5432/iotdb
- PG_USER=iot
- PG_PASSWORD=iotpass
- PG_TABLE=anomalies

InfluxDB:
- WRITE_TO_INFLUX=true|false
- INFLUX_URL=http://influxdb:8086
- INFLUX_ORG=iot-org
- INFLUX_BUCKET=iot-bucket
- INFLUX_TOKEN=iot-token-123
- INFLUX_PRECISION=ns
"""

import os
import math
import requests
from typing import Iterable, List

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, to_timestamp, window, avg, stddev_pop,
    abs as sql_abs, lit, explode, map_keys, map_values,
    first, when
)
from pyspark.sql.types import StructType, StructField, StringType, MapType, DoubleType


# ----------------------------
# Config
# ----------------------------
APP_NAME = os.getenv("APP_NAME", "iot-anomaly-streaming")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot.sensor.raw")
STARTING_OFFSETS = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

WINDOW_DURATION = os.getenv("WINDOW_DURATION", "1 minute")
WATERMARK_DELAY = os.getenv("WATERMARK_DELAY", "2 minutes")

Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "3.0"))
MIN_STD = float(os.getenv("MIN_STD", "0.05"))

CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoints/iot_anomaly_v2")

# Postgres (event-level anomalies only)
WRITE_TO_POSTGRES = os.getenv("WRITE_TO_POSTGRES", "false").lower() == "true"
PG_URL = os.getenv("PG_URL", "jdbc:postgresql://postgres:5432/iotdb")
PG_USER = os.getenv("PG_USER", "iot")
PG_PASSWORD = os.getenv("PG_PASSWORD", "iotpass")
PG_TABLE = os.getenv("PG_TABLE", "anomalies")

# InfluxDB 2.x via HTTP
WRITE_TO_INFLUX = os.getenv("WRITE_TO_INFLUX", "true").lower() == "true"
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_ORG = os.getenv("INFLUX_ORG", "iot-org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "iot-bucket")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "iot-token-123")
INFLUX_PRECISION = os.getenv("INFLUX_PRECISION", "ns")

MEASUREMENT_METRICS = os.getenv("INFLUX_MEAS_METRICS", "sensor_metrics")
MEASUREMENT_ANOMS = os.getenv("INFLUX_MEAS_ANOMS", "sensor_anomalies")

# Keep requests sessions for efficiency
_http = requests.Session()


# ----------------------------
# Helpers: Spark
# ----------------------------
def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName(APP_NAME)
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def sensor_schema() -> StructType:
    return StructType([
        StructField("ts", StringType(), True),  # ISO-8601 string
        StructField("device_id", StringType(), True),
        StructField("location", StringType(), True),
        StructField("model", StringType(), True),
        StructField("metrics", MapType(StringType(), DoubleType()), True),
    ])


# ----------------------------
# Helpers: Influx line protocol
# ----------------------------
def _escape_tag_value(v: str) -> str:
    # Influx line protocol escaping for tag values/keys: commas, spaces, equals
    return (
        str(v)
        .replace("\\", "\\\\")
        .replace(" ", "\\ ")
        .replace(",", "\\,")
        .replace("=", "\\=")
    )


def _format_field_value(v) -> str:
    # floats -> keep as is; ints -> append i; booleans -> true/false; strings -> quoted
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}i"
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return ""
        return repr(float(v))
    # string
    s = str(v).replace('"', '\\"')
    return f"\"{s}\""


def _to_ns(ts) -> int:
    # ts is python datetime
    # Spark TimestampType comes to Python as datetime.datetime
    return int(ts.timestamp() * 1_000_000_000)


def influx_write_lines(lines: List[str]) -> None:
    if not lines:
        return

    url = f"{INFLUX_URL.rstrip('/')}/api/v2/write"
    params = {
        "org": INFLUX_ORG,
        "bucket": INFLUX_BUCKET,
        "precision": INFLUX_PRECISION,
    }
    headers = {
        "Authorization": f"Token {INFLUX_TOKEN}",
        "Content-Type": "text/plain; charset=utf-8",
    }

    # Influx recommends batches; keep it simple for demo
    payload = "\n".join(lines)
    resp = _http.post(url, params=params, headers=headers, data=payload, timeout=10)
    if resp.status_code >= 300:
        raise RuntimeError(f"Influx write failed: {resp.status_code} {resp.text[:500]}")


# ----------------------------
# foreachBatch writers
# ----------------------------
def write_to_postgres(anoms_df: DataFrame) -> None:
    """
    anoms_df schema expected:
    ts (TimestampType), device_id, metric, value, score, method, severity
    """
    (
        anoms_df
        .select("ts", "device_id", "metric", "value", "score", "method", "severity")
        .write
        .format("jdbc")
        .option("url", PG_URL)
        .option("dbtable", PG_TABLE)
        .option("user", PG_USER)
        .option("password", PG_PASSWORD)
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save()
    )


def foreach_batch_writer(batch_df: DataFrame, batch_id: int) -> None:
    """
    batch_df contains *all metrics rows* with z-score columns.
    We write:
    - Influx: metrics (wide) + anomalies (only anomalous rows)
    - Postgres: anomalies only
    """
    if batch_df is None:
        return

    # Avoid empty batches
    if batch_df.rdd.isEmpty():
        return

    # ----------------------------
    # Prepare anomalies (event-level)
    # ----------------------------
    anoms = (
        batch_df
        .withColumn("method", lit("zscore"))
        .withColumn(
            "severity",
            when(col("abs_z") >= lit(8.0), lit("critical"))
            .when(col("abs_z") >= lit(5.0), lit("high"))
            .when(col("abs_z") >= lit(3.0), lit("medium"))
            .otherwise(lit("low"))
        )
        .filter(col("abs_z") >= lit(Z_THRESHOLD))
        .select(
            col("ts"),
            col("device_id"),
            col("location"),
            col("model"),
            col("metric"),
            col("value").cast("double").alias("value"),
            col("zscore").cast("double").alias("score"),
            col("method"),
            col("severity"),
        )
    )

    # ----------------------------
    # Write Postgres
    # ----------------------------
    if WRITE_TO_POSTGRES:
        write_to_postgres(anoms)

    # ----------------------------
    # Write InfluxDB (line protocol via driver)
    # ----------------------------
    if WRITE_TO_INFLUX:
        # Collect only what we need (demo scale). If you have huge throughput, this must be replaced
        # with a proper connector or partitioned HTTP writes.
        metrics_rows = (
            batch_df
            .select("ts", "device_id", "location", "model", "metric", "value")
            .collect()
        )

        anom_rows = (
            anoms
            .select("ts", "device_id", "location", "model", "metric", "value", "score", "severity")
            .collect()
        )

        metric_lines: List[str] = []
        anom_lines: List[str] = []

        # Build "wide" metrics by (ts, device_id, location, model)
        # We'll aggregate in python to generate one line with multiple fields (temperature=...,humidity=...)
        # Key: (ts_ns, tags_tuple)
        wide = {}
        for r in metrics_rows:
            if r["ts"] is None:
                continue
            ts_ns = _to_ns(r["ts"])
            tags = (
                ("device_id", r["device_id"] or "unknown"),
                ("location", r["location"] or "unknown"),
                ("model", r["model"] or "unknown"),
            )
            k = (ts_ns, tags)
            if k not in wide:
                wide[k] = {}
            m = r["metric"]
            v = r["value"]
            if m is not None and v is not None:
                wide[k][m] = float(v)

        for (ts_ns, tags), fields in wide.items():
            if not fields:
                continue
            tag_str = ",".join([f"{k}={_escape_tag_value(v)}" for k, v in tags])
            # Only numeric fields
            field_parts = []
            for fk, fv in fields.items():
                fv_s = _format_field_value(fv)
                if fv_s != "":
                    field_parts.append(f"{_escape_tag_value(fk)}={fv_s}")
            if not field_parts:
                continue
            field_str = ",".join(field_parts)
            metric_lines.append(f"{MEASUREMENT_METRICS},{tag_str} {field_str} {ts_ns}")

        for r in anom_rows:
            if r["ts"] is None:
                continue
            ts_ns = _to_ns(r["ts"])
            tags = [
                ("device_id", r["device_id"] or "unknown"),
                ("location", r["location"] or "unknown"),
                ("model", r["model"] or "unknown"),
                ("metric", r["metric"] or "unknown"),
                ("severity", r["severity"] or "unknown"),
            ]
            tag_str = ",".join([f"{k}={_escape_tag_value(v)}" for k, v in tags])

            v_s = _format_field_value(float(r["value"]) if r["value"] is not None else None)
            s_s = _format_field_value(float(r["score"]) if r["score"] is not None else None)

            field_parts = []
            if v_s != "":
                field_parts.append(f"value={v_s}")
            if s_s != "":
                field_parts.append(f"score={s_s}")

            if field_parts:
                anom_lines.append(f"{MEASUREMENT_ANOMS},{tag_str} {','.join(field_parts)} {ts_ns}")

        # Send in 2 writes (metrics + anomalies)
        influx_write_lines(metric_lines)
        influx_write_lines(anom_lines)


# ----------------------------
# Main pipeline
# ----------------------------
def main() -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel(os.getenv("SPARK_LOG_LEVEL", "WARN"))

    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", STARTING_OFFSETS)
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed = (
        raw.selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), sensor_schema()).alias("data"))
        .select("data.*")
        .withColumn("ts", to_timestamp(col("ts")))
        .filter(col("ts").isNotNull() & col("device_id").isNotNull() & col("metrics").isNotNull())
    )

    # Explode metrics map -> rows
    # Output: ts, device_id, location, model, metric, value
    metrics_rows = (
        parsed
        .select(
            "ts", "device_id", "location", "model",
            explode(col("metrics")).alias("metric", "value")
        )
        .filter(col("metric").isNotNull())
    )

    # Rolling stats per (device_id, metric) in event-time windows
    stats = (
        metrics_rows
        .withWatermark("ts", WATERMARK_DELAY)
        .groupBy(
            window(col("ts"), WINDOW_DURATION).alias("w"),
            col("device_id"),
            col("metric"),
            col("location"),
            col("model"),
        )
        .agg(
            avg(col("value")).alias("mean"),
            stddev_pop(col("value")).alias("std")
        )
    )

    # Join stats back to events by window (same window bucket) to compute z-score
    # We derive window for each event to join deterministically.
    events_with_w = (
        metrics_rows
        .withColumn("w", window(col("ts"), WINDOW_DURATION))
    )

    joined = (
        events_with_w
        .join(
            stats,
            on=["w", "device_id", "metric", "location", "model"],
            how="left"
        )
        .withColumn("std_safe", when(col("std").isNull() | (col("std") < lit(MIN_STD)), lit(MIN_STD)).otherwise(col("std")))
        .withColumn("zscore", (col("value") - col("mean")) / col("std_safe"))
        .withColumn("abs_z", sql_abs(col("zscore")))
        .drop("std_safe")
    )

    # Streaming sink: foreachBatch so we can fan-out to Postgres + Influx
    query = (
        joined.writeStream
        .outputMode("append")
        .foreachBatch(foreach_batch_writer)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
