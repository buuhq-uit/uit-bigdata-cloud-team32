from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, to_date

from config import APP_NAME, KAFKA_BOOTSTRAP, KAFKA_TOPIC, MAX_OFFSETS_PER_TRIGGER, STARTING_OFFSETS, RAW_S3_PATH, CHECKPOINT
from schema import sensor_schema

def build_spark() -> SparkSession:
    return SparkSession.builder.appName(APP_NAME).getOrCreate()

def run() -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", STARTING_OFFSETS)
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", str(MAX_OFFSETS_PER_TRIGGER))
        .load()
    )

    raw_df = (
        kafka_df.selectExpr("CAST(value AS STRING) AS json_str")
        .select(from_json(col("json_str"), sensor_schema()).alias("j"))
        .select("j.*")
        .withColumn("event_ts", to_timestamp(col("ts")))
        .withColumn("dt", to_date(col("event_ts")))
    )

    def write_to_minio(batch_df, batch_id: int):
        (batch_df
            .dropna(subset=["device_id"])
            .write
            .mode("append")
            .partitionBy("dt")
            .parquet(RAW_S3_PATH)
        )

    query = (
        raw_df.writeStream
        .foreachBatch(write_to_minio)
        .option("checkpointLocation", CHECKPOINT)
        .start()
    )

    query.awaitTermination()