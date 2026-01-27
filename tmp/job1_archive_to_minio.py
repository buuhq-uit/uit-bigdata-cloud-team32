# spark-app/archive_raw_to_minio.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, to_date
from pyspark.sql.types import StructType, StructField, StringType, MapType, DoubleType

KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC = "iot.sensor.raw"

# MinIO (S3A)
RAW_S3_PATH = "s3a://iot-datalake/raw"          # data lake raw zone
CHECKPOINT = "/tmp/spark-checkpoints/archive_raw_to_minio"

schema = StructType([
    StructField("ts", StringType(), True),
    StructField("device_id", StringType(), True),
    StructField("location", StringType(), True),
    StructField("model", StringType(), True),
    StructField("metrics", MapType(StringType(), DoubleType()), True),
])

spark = (
    SparkSession.builder
    .appName("archive-raw-kafka-to-minio")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# Read Kafka
kafka_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
)

# Parse JSON
raw_df = (
    kafka_df.selectExpr("CAST(value AS STRING) AS json_str")
    .select(from_json(col("json_str"), schema).alias("j"))
    .select("j.*")
    .withColumn("event_ts", to_timestamp(col("ts")))   # parsed timestamp
    .withColumn("dt", to_date(col("event_ts")))        # partition key (date)
)

# Use foreachBatch to control partitioned append writes
def write_to_minio(batch_df, batch_id: int):
    (batch_df
        .dropna(subset=["device_id"])   # tiny safety
        .write
        .mode("append")
        .partitionBy("dt")              # raw/dt=YYYY-MM-DD/...
        .parquet(RAW_S3_PATH)
    )

query = (
    raw_df.writeStream
    .foreachBatch(write_to_minio)
    .option("checkpointLocation", CHECKPOINT)
    .start()
)

query.awaitTermination()
