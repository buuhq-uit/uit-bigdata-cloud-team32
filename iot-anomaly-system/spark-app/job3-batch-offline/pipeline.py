import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, avg, stddev, count
from config import APP_NAME, RAW_S3_PATH, OUT_S3_PATH

def build_spark() -> SparkSession:
    return SparkSession.builder.appName(APP_NAME).getOrCreate()

def run() -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    raw = spark.read.parquet(RAW_S3_PATH)

    flat = (
        raw.select("dt", "device_id", explode(col("metrics")).alias("metric", "value"))
        .where(col("value").isNotNull())
    )

    stats = (
        flat.groupBy("dt", "device_id", "metric")
        .agg(
            count("*").alias("n"),
            avg("value").alias("mean"),
            stddev("value").alias("stddev"),
        )
    )

    (stats.write
        .mode("overwrite")
        .partitionBy("dt")
        .parquet(OUT_S3_PATH)
    )

    print("✅ Offline stats written to:", OUT_S3_PATH)