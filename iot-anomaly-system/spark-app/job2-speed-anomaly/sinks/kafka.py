from pyspark.sql import DataFrame
from config import KAFKA_BOOTSTRAP, KAFKA_TOPIC_ANOMALY

def write_anoms_to_kafka(anoms_df: DataFrame) -> None:
    kafka_df = (
        anoms_df
        .selectExpr(
            "CAST(NULL AS STRING) AS key",
            "to_json(named_struct("
            "  'ts', CAST(ts AS STRING),"
            "  'device_id', device_id,"
            "  'location', location,"
            "  'model', model,"
            "  'metric', metric,"
            "  'value', value,"
            "  'score', score,"
            "  'severity', severity,"
            "  'is_anomaly', 1"
            ")) AS value"
        )
    )
    if not kafka_df.rdd.isEmpty():
        (
            kafka_df.write
            .format("kafka")
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
            .option("topic", KAFKA_TOPIC_ANOMALY)
            .save()
        )