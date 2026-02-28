from pyspark.ml.clustering import KMeansModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import functions as F
from functools import reduce
from pyspark.sql.functions import when, col
from src.utils.data_utils import convert_to_4_scale

class StudentPredictorService:

    MODEL_PATH = "models/kmeans_model"

    @staticmethod
    def predict_students(spark_df, spark):

        # ===== Load model =====
        model = KMeansModel.load(StudentPredictorService.MODEL_PATH)

        # ===== Feature engineering =====
        from pyspark.sql.functions import avg, stddev, sum, when

        subject_cols = [
            c for c in spark_df.columns
            if c not in ["ma_sv", "ho_ten"]
        ]

        # Tính feature
        agg_expr = []

        for c in subject_cols:
            agg_expr.append(col(c))

        df_features = spark_df.select(
            "ma_sv",
            "ho_ten",
            *agg_expr
        )

        # GPA
        gpa_expr = reduce(
            lambda x, y: x + y,
            [convert_to_4_scale(c) for c in subject_cols]
        ) / len(subject_cols)

        df_features = df_features.withColumn("gpa", gpa_expr)

        # Failed subjects (<4)
        failed_expr = reduce(
            lambda x, y: x + y,
            [when(col(c) < 4, 1).otherwise(0) for c in subject_cols]
        )
        df_features = df_features.withColumn(
            "failed_subjects",
            failed_expr
        )

        # Excellent subjects (>=8)
        excellent_expr = reduce(
            lambda x, y: x + y,
            [when(col(c) >= 8, 1).otherwise(0) for c in subject_cols]
        )
        df_features = df_features.withColumn(
            "excellent_subjects",
            excellent_expr
        )

        # Std deviation
        variance_expr = reduce(
            lambda x, y: x + y,
            [(convert_to_4_scale(c) - F.col("gpa"))**2 for c in subject_cols]
        ) / len(subject_cols)

        df_features = df_features.withColumn(
            "std_score",
            F.sqrt(variance_expr)
        )

        df_final = df_features.select(
            "ma_sv",
            "ho_ten",
            "gpa",
            "std_score",
            "failed_subjects",
            "excellent_subjects"
        )

        assembler = VectorAssembler(
            inputCols=[
                "gpa",
                "std_score",
                "failed_subjects",
                "excellent_subjects"
            ],
            outputCol="features"
        )

        data = assembler.transform(df_final)

        result = model.transform(data)

        # Mapping mức độ
        risk_mapping = {
            2: 0,  # Nguy hiểm 
            0: 1,  # Trung bình
            3: 2,  # Khá
            1: 3   # Xuất sắc
        }

        mapping_list = []
        for k, v in risk_mapping.items():
            mapping_list.extend([F.lit(k), F.lit(v)])
        map_expr = F.create_map(mapping_list)

        result = result.withColumn(
            "risk_order",
            map_expr[col("prediction")]
        )

        result = result.orderBy("risk_order")
        result = result \
        .withColumn("gpa", F.round("gpa", 1)) \
        .withColumn("std_score", F.round("std_score", 1))
        return result.drop("features", "risk_order")