from pyspark.ml.clustering import KMeansModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import col
from pyspark.sql import functions as F


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
        gpa_expr = sum([col(c) for c in subject_cols]) / len(subject_cols)

        df_features = df_features.withColumn("gpa", gpa_expr)

        # Failed subjects (<4)
        df_features = df_features.withColumn(
            "failed_subjects",
            sum([
                when(col(c) < 4, 1).otherwise(0)
                for c in subject_cols
            ])
        )

        # Excellent subjects (>=8)
        df_features = df_features.withColumn(
            "excellent_subjects",
            sum([
                when(col(c) >= 8, 1).otherwise(0)
                for c in subject_cols
            ])
        )

        # Std deviation
        df_features = df_features.withColumn(
            "std_score",
            F.sqrt(
                sum([(col(c) - col("gpa"))**2 for c in subject_cols]) / len(subject_cols)
            )
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
            1: 1,  # Trung bình
            0: 2,  # Khá
            3: 3   # Xuất sắc
        }

        map_expr = F.create_map(
            [F.lit(x) for x in sum(risk_mapping.items(), ())]
        )

        result = result.withColumn(
            "risk_order",
            map_expr[col("prediction")]
        )

        result = result.orderBy("risk_order")

        return result.drop("features", "risk_order")