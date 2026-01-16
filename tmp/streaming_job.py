# /opt/spark-app/streaming_job.py
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_timestamp, regexp_replace, coalesce,
    window, avg, stddev_pop, abs as sql_abs, lit
)
from pyspark.sql.types import StructType, StructField, StringType, MapType, DoubleType

APP_NAME = os.getenv("APP_NAME", "iot-anomaly-streaming")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot.sensor.raw")
STARTING_OFFSETS = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

# windows / watermark
WINDOW_DURATION = os.getenv("WINDOW_DURATION", "1 minute")      # baseline window
WATERMARK_DELAY = os.getenv("WATERMARK_DELAY", "2 minutes")     # lateness tolerance

# anomaly thresholds
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "3.0"))            # default z-score threshold
MIN_STD = float(os.getenv("MIN_STD", "0.05"))                   # avoid divide-by-zero

CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoints/iot_anomaly")

# Optional: write to Postgres using foreachBatch (enable by env WRITE_TO_POSTGRES=true)
WRITE_TO_POSTGRES = os.getenv("WRITE_TO_POSTGRES", "false").lower() == "true"
PG_URL = os.getenv("PG_URL", "jdbc:postgresql://postgres:5432/iotdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_TABLE = os.getenv("PG_TABLE", "anomalies")


def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName(APP_NAME)
        # Spark SQL config
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    schema = StructType([
        StructField("ts", StringType(), True),
        StructField("device_id", StringType(), True),
        StructField("location", StringType(), True),
        StructField("model", StringType(), True),
        StructField("metrics", MapType(StringType(), DoubleType(), True), True),
    ])

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", STARTING_OFFSETS)
        .load()
    )

    json_df = raw.selectExpr("CAST(value AS STRING) AS value_str")

    parsed = json_df.select(from_json(col("value_str"), schema).alias("json")).select("json.*")

    # Normalize timestamp:
    # - replace trailing 'Z' => '+00:00' for consistent parsing
    # - parse with microseconds + timezone first, fallback to second-level
    ts_norm = regexp_replace(col("ts"), r"Z$", "+00:00")

    event_ts = coalesce(
        to_timestamp(ts_norm, "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX"),
        to_timestamp(ts_norm, "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"),
        to_timestamp(ts_norm, "yyyy-MM-dd'T'HH:mm:ssXXX"),
        to_timestamp(ts_norm)  # last resort
    )

    events = (
        parsed
        .withColumn("event_ts", event_ts)
        .withColumn("temperature", col("metrics")["temperature"].cast("double"))
        .withColumn("humidity", col("metrics")["humidity"].cast("double"))
        .drop("metrics")
        .filter(col("device_id").isNotNull() & col("event_ts").isNotNull() & col("temperature").isNotNull())
        .withWatermark("event_ts", WATERMARK_DELAY)
    )

    # Baseline stats per device per window (no join needed)
    stats = (
        events
        .groupBy(window(col("event_ts"), WINDOW_DURATION).alias("w"), col("device_id"))
        .agg(
            avg(col("temperature")).alias("temp_mean"),
            stddev_pop(col("temperature")).alias("temp_std"),
            avg(col("humidity")).alias("hum_mean"),
            stddev_pop(col("humidity")).alias("hum_std"),
        )
    )

    # Attach anomaly signal at window level:
    # Here we flag the WINDOW if mean temperature is abnormal vs its own std is not meaningful.
    # Better approach: evaluate anomaly at event-level requires joining events -> window stats.
    # We'll output window-level anomalies (simple + stable for streaming).
    #
    # If you really want event-level anomalies, we can do it with:
    #  - outputMode("append")
    #  - watermark on both sides
    #  - join events with stats on (device_id and event_ts within window)
    # But your earlier error was because outputMode was Update. Append will work.
    #
    # For now: window-level anomaly based on std, and mean exceeding a fixed threshold is optional.
    # We'll compute a "z-like" signal using std floor.
    temp_std_safe = (col("temp_std").isNull() | (col("temp_std") < lit(MIN_STD)))
    hum_std_safe = (col("hum_std").isNull() | (col("hum_std") < lit(MIN_STD)))

    # Flag if variability spikes (std) OR mean exceeds a hard ceiling (optional)
    # For demo, we mark anomaly when mean temp >= 40 OR std >= 5
    anomalies = (
        stats
        .withColumn("temp_std_safe", temp_std_safe)
        .withColumn("hum_std_safe", hum_std_safe)
        .withColumn("is_anomaly",
                    (col("temp_mean") >= lit(40.0)) | (col("temp_std") >= lit(5.0)))
        .filter(col("is_anomaly"))
        .select(
            col("w.start").alias("window_start"),
            col("w.end").alias("window_end"),
            col("device_id"),
            col("temp_mean"),
            col("temp_std"),
            col("hum_mean"),
            col("hum_std"),
            col("is_anomaly"),
        )
    )

    if WRITE_TO_POSTGRES:
        def write_pg(batch_df, batch_id: int):
            (
                batch_df
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

        query = (
            anomalies.writeStream
            .outputMode("append")
            .foreachBatch(write_pg)
            .option("checkpointLocation", CHECKPOINT_DIR)
            .start()
        )
    else:
        query = (
            anomalies.writeStream
            .outputMode("append")
            .format("console")
            .option("truncate", "false")
            .option("checkpointLocation", CHECKPOINT_DIR)
            .start()
        )

    query.awaitTermination()


if __name__ == "__main__":
    main()
