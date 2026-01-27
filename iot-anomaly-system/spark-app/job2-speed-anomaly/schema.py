from pyspark.sql.types import StructType, StructField, StringType, MapType, DoubleType

def sensor_schema() -> StructType:
    return StructType([
        StructField("ts", StringType(), True),
        StructField("device_id", StringType(), True),
        StructField("location", StringType(), True),
        StructField("model", StringType(), True),
        StructField("metrics", MapType(StringType(), DoubleType()), True),
    ])