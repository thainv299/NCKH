from pyspark.sql.functions import avg, stddev, sum, when, col

def create_features(fact_score):
    features = fact_score.groupBy("ma_sv").agg(
        avg("diem").alias("gpa"),
        stddev("diem").alias("std_score"),
        sum(when(col("diem") < 5, 1).otherwise(0)).alias("failed_subjects"),
        sum(when(col("diem") >= 8, 1).otherwise(0)).alias("excellent_subjects")
    )

    return features