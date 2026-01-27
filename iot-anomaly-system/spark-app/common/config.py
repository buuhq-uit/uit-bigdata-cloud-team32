# common/config.py
import os
import os.path as osp

def env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() == "true"

# Kafka
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", os.getenv("KAFKA_TOPIC", "iot.sensor.raw"))
KAFKA_TOPIC_ANOMALY = os.getenv("KAFKA_TOPIC_ANOMALY", "iot.sensor.anomaly")
STARTING_OFFSETS = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

# S3/MinIO
RAW_S3_PATH = os.getenv("RAW_S3_PATH", "s3a://iot-datalake/raw")
OFFLINE_STATS_S3_PATH = os.getenv("OFFLINE_STATS_S3_PATH", os.getenv("OUT_S3_PATH", "s3a://iot-datalake/offline_stats"))

# Checkpoints
CHECKPOINT_BASE_DIR = os.getenv("CHECKPOINT_BASE_DIR", os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoints"))
def checkpoint_dir(job_key: str) -> str:
    explicit = os.getenv("CHECKPOINT_DIR")
    base = explicit if explicit else CHECKPOINT_BASE_DIR
    return os.getenv(f"{job_key.upper()}_CHECKPOINT_DIR", osp.join(base, job_key))

# Postgres
PG_URL = os.getenv("PG_URL", "jdbc:postgresql://postgres:5432/iotdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "P@sswordDb#Pi!2025")
PG_TABLE = os.getenv("PG_TABLE", "anomalies")

# InfluxDB
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_ORG = os.getenv("INFLUX_ORG", "iot-org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "iot-bucket")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "iot-token-123")
INFLUX_PRECISION = os.getenv("INFLUX_PRECISION", "ns")
MEASUREMENT_METRICS = os.getenv("INFLUX_MEAS_METRICS", "sensor_metrics")
MEASUREMENT_ANOMS = os.getenv("INFLUX_MEAS_ANOMS", "sensor_anomalies")