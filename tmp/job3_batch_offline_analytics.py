# spark-app/batch_offline_analytics.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, avg, stddev, count

RAW_S3_PATH = "s3a://iot-datalake/raw"      # parquet partitioned by dt
OUT_S3_PATH = "s3a://iot-datalake/offline_stats"  # output stats

spark = SparkSession.builder.appName("batch-offline-analytics").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Read raw parquet (partitioned)
raw = spark.read.parquet(RAW_S3_PATH)

# Flatten metrics: (dt, device_id, metric, value)
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

# Save thresholds/statistics to MinIO
(stats.write
    .mode("overwrite")              # overwrite whole offline_stats each run (simple)
    .partitionBy("dt")
    .parquet(OUT_S3_PATH)
)

print("✅ Offline stats written to:", OUT_S3_PATH)
