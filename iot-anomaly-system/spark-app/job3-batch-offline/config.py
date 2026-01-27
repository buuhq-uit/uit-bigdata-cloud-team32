import os

APP_NAME = os.getenv("APP_NAME", "batch-offline-analytics")
RAW_S3_PATH = os.getenv("RAW_S3_PATH", "s3a://iot-datalake/raw")
OUT_S3_PATH = os.getenv("OUT_S3_PATH", "s3a://iot-datalake/offline_stats")