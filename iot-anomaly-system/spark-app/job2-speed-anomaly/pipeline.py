from pyspark.sql.functions import lit, when, col
from pyspark.sql import DataFrame

from config import (
    APP_NAME, Z_THRESHOLD, CHECKPOINT_DIR,
    WRITE_TO_POSTGRES, WRITE_TO_INFLUX, WRITE_TO_KAFKA
)
from spark_utils import build_spark, read_kafka, parse_events, explode_metrics, with_zscore
from sinks.influx import write_lines, build_metric_lines, build_anom_lines
from sinks.postgres import write_to_postgres
from sinks.kafka import write_anoms_to_kafka

def foreach_batch_writer(batch_df: DataFrame, batch_id: int) -> None:
    if batch_df is None or batch_df.rdd.isEmpty():
        return

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

    if WRITE_TO_POSTGRES:
        write_to_postgres(anoms)

    if WRITE_TO_KAFKA:
        try:
            write_anoms_to_kafka(anoms)
        except Exception as e:
            print(f"[WARN] Failed to write anomalies to Kafka: {e}")

    if WRITE_TO_INFLUX:
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
        write_lines(build_metric_lines(metrics_rows))
        write_lines(build_anom_lines(anom_rows))

def run() -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    raw = read_kafka(spark)
    parsed = parse_events(raw)
    metrics_rows = explode_metrics(parsed)
    joined = with_zscore(metrics_rows)

    query = (
        joined.writeStream
        .outputMode("append")
        .foreachBatch(foreach_batch_writer)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .start()
    )
    query.awaitTermination()