from pyspark.sql import DataFrame
from config import PG_URL, PG_USER, PG_PASSWORD, PG_TABLE

def write_to_postgres(anoms_df: DataFrame) -> None:
    (
        anoms_df
        .select("ts", "device_id", "metric", "value", "score", "method", "severity")
        .write
        .format("jdbc")
        .option("url", PG_URL)
        .option("dbtable", PG_TABLE)
        .option("user", PG_USER)
        .option("password", PG_PASSWORD)
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save()
    )