from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, to_timestamp, window, avg, stddev_pop,
    abs as sql_abs, lit, explode, when
)

from config import APP_NAME, KAFKA_BOOTSTRAP, KAFKA_TOPIC, MAX_OFFSETS_PER_TRIGGER, STARTING_OFFSETS, WINDOW_DURATION, WATERMARK_DELAY, MIN_STD
from schema import sensor_schema

def build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName(APP_NAME)
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

def read_kafka(spark: SparkSession) -> DataFrame:
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", STARTING_OFFSETS)
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", MAX_OFFSETS_PER_TRIGGER)
        .load()
    )

def parse_events(raw: DataFrame) -> DataFrame:
    return (
        raw.selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), sensor_schema()).alias("data"))
        .select("data.*")
        .withColumn("ts", to_timestamp(col("ts")))
        .filter(col("ts").isNotNull() & col("device_id").isNotNull() & col("metrics").isNotNull())
    )

def explode_metrics(parsed: DataFrame) -> DataFrame:
    return (
        parsed
        .select(
            "ts", "device_id", "location", "model",
            explode(col("metrics")).alias("metric", "value")
        )
        .filter(col("metric").isNotNull())
    )

def with_zscore(metrics_rows: DataFrame) -> DataFrame:
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

    events_with_w = metrics_rows.withColumn("w", window(col("ts"), WINDOW_DURATION))

    joined = (
        events_with_w
        .join(stats, on=["w", "device_id", "metric", "location", "model"], how="left")
        .withColumn("std_safe", when(col("std").isNull() | (col("std") < lit(MIN_STD)), lit(MIN_STD)).otherwise(col("std")))
        .withColumn("zscore", (col("value") - col("mean")) / col("std_safe"))
        .withColumn("abs_z", sql_abs(col("zscore")))
        .drop("std_safe")
    )
    return joined