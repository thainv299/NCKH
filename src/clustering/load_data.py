from pyspark.sql import SparkSession

def load_data(path):
    spark = SparkSession.builder \
        .appName("StudentBigData") \
        .getOrCreate()

    df = spark.read.csv(
        path,
        header=True,
        sep = ";",
        inferSchema=True
    )

    return spark, df