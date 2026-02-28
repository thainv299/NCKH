from pyspark.sql.functions import avg, stddev, sum, when, col
from src.utils.data_utils import convert_to_4_scale

def create_features(fact_score):
    fact_score = fact_score.withColumn(
        "diem_he4",
        convert_to_4_scale("diem")
    )
    features = fact_score.groupBy("ma_sv").agg(
        avg("diem_he4").alias("gpa"),
        stddev("diem_he4").alias("std_score"),
        sum(when(col("diem_he4") < 1.0, 1).otherwise(0)).alias("failed_subjects"),
        sum(when(col("diem_he4") >= 3.5, 1).otherwise(0)).alias("excellent_subjects")
    )

    return features