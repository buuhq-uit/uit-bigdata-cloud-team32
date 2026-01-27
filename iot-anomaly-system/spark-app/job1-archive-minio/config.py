import os
from common.config import (
    KAFKA_BOOTSTRAP, KAFKA_TOPIC_RAW, STARTING_OFFSETS,
    RAW_S3_PATH as COMMON_RAW_S3_PATH, checkpoint_dir
)

APP_NAME = os.getenv("APP_NAME", "archive-raw-kafka-to-minio")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", KAFKA_TOPIC_RAW)
STARTING_OFFSETS = STARTING_OFFSETS
KAFKA_BOOTSTRAP = KAFKA_BOOTSTRAP

RAW_S3_PATH = os.getenv("RAW_S3_PATH", COMMON_RAW_S3_PATH)
CHECKPOINT = checkpoint_dir("archive_raw_to_minio")

MAX_OFFSETS_PER_TRIGGER = int(os.getenv("MAX_OFFSETS_PER_TRIGGER", "1000"))