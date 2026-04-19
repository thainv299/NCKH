import os
from pyspark.ml.clustering import KMeansModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import functions as F
from functools import reduce
from src.utils.data_utils import convert_to_4_scale

class RiskClustering:
    @staticmethod
    def cluster(spark_df):
        """
        Dự đoán rủi ro học tập bằng thuật toán KMeans k=4.
        """
        # Định tuyến lấy mô hình pre-trained
        # Cấu trúc: d:\NCKH\src\ml\unsupervised\risk_clustering.py
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "models", "kmeans_model"
        )
        
        try:
            model = KMeansModel.load(model_path)
        except Exception as e:
            # Nếu không thể load tự động trả về df chưa dự đoán
            print(f"Không thể tải mô hình Risk: {e}")
            return spark_df

        subject_cols = [c for c in spark_df.columns if c not in ["ma_sv", "ho_ten", "TOEIC"]]

        agg_expr = [F.col(c) for c in subject_cols]
        df_features = spark_df.select("ma_sv", "ho_ten", *agg_expr)

        # 1. Điểm trung bình (GPA)
        gpa_expr = reduce(
            lambda x, y: x + y,
            [convert_to_4_scale(c) for c in subject_cols]
        ) / len(subject_cols)
        df_features = df_features.withColumn("gpa", gpa_expr)

        # 2. Số lượng môn bị rớt (Failed subjects)
        failed_expr = reduce(
            lambda x, y: x + y,
            [F.when(F.col(c) < 4, 1).otherwise(0) for c in subject_cols]
        )
        df_features = df_features.withColumn("failed_subjects", failed_expr)

        # 3. Số lượng môn bị xuất sắc (Excellent subjects)
        excellent_expr = reduce(
            lambda x, y: x + y,
            [F.when(F.col(c) >= 8, 1).otherwise(0) for c in subject_cols]
        )
        df_features = df_features.withColumn("excellent_subjects", excellent_expr)

        # 4. Độ lệch chuẩn (Std deviation)
        variance_expr = reduce(
            lambda x, y: x + y,
            [(convert_to_4_scale(c) - F.col("gpa"))**2 for c in subject_cols]
        ) / len(subject_cols)
        df_features = df_features.withColumn("std_score", F.sqrt(variance_expr))

        df_final = df_features.select("ma_sv", "ho_ten", "gpa", "std_score", "failed_subjects", "excellent_subjects")

        assembler = VectorAssembler(
            inputCols=["gpa", "std_score", "failed_subjects", "excellent_subjects"],
            outputCol="features"
        )

        data = assembler.transform(df_final)
        result = model.transform(data)

        # Mapping mức độ rủi ro (Theo ID cụm được đào tạo trước đó của người dùng)
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

        result = result.withColumn("risk_order", map_expr[F.col("prediction")])
        result = result.orderBy("risk_order")
        
        result = result \
            .withColumn("gpa", F.round("gpa", 2)) \
            .withColumn("std_score", F.round("std_score", 2))
            
        return result.drop("features", "risk_order")
