import os
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans, KMeansModel

class ReadinessClustering:
    @staticmethod
    def cluster(df, k=3, seed=42, model_path=None):
        """
        Đánh giá tính sẵn sàng bằng cách dùng mô hình KMeans tuyệt đối (Pre-trained)
        hoặc fallback về fit-on-the-fly.
        """
        feature_cols = ["gpa_tong", "TOEIC"]
        if "TOEIC" not in df.columns:
            df = df.withColumn("TOEIC", F.lit(0.0))

        for c in feature_cols:
            df = df.withColumn(c, F.coalesce(F.col(c).cast(DoubleType()), F.lit(0.0)))

        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
        df_vec = assembler.transform(df)

        # Nếu không có model_path, dùng mặc định
        if not model_path:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "models", "career_readiness_kmeans_model"
            )
        
        try:
            model = KMeansModel.load(model_path)
            df_clustered = model.transform(df_vec)
        except Exception as e:
            print(f"Không thể tải mô hình nghề nghiệp từ {model_path}, fitting new: {e}")
            kmeans = KMeans(k=k, seed=seed, featuresCol="features", predictionCol="cluster")
            model = kmeans.fit(df_vec)
            df_clustered = model.transform(df_vec)

        # Gán nhãn KMeans dựa trên việc sắp xếp tâm cụm (GPA cao = Sẵn sàng cao)
        centers = model.clusterCenters()
        cluster_gpa = [(i, float(c[0])) for i, c in enumerate(centers)]
        cluster_gpa.sort(key=lambda x: x[1], reverse=True)

        labels = ["San sang cao", "Dang phat trien", "Chua san sang"]
        mapping_expr = F.lit("Chua xac dinh")
        for rank, (cid, _) in enumerate(cluster_gpa):
            label = labels[rank] if rank < len(labels) else labels[-1]
            mapping_expr = F.when(F.col("cluster") == cid, F.lit(label)).otherwise(mapping_expr)

        df_clustered = df_clustered.withColumn("nhom_san_sang", mapping_expr)
        return df_clustered.drop("features")
