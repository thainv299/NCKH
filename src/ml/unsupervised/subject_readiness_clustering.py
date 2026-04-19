"""
Phân loại chất lượng môn học bằng KMeans k=4
"""
import os
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans, KMeansModel


class SubjectReadinessClustering:
    """KMeans clustering phân loại chất lượng môn học"""

    @staticmethod
    def cluster(sdf, k=4, seed=42, model_path=None):
        """
        Phân loại môn học thành 4 nhóm: Tiêu cực, Không ổn định, Ổn định, Xuất sắc
        """
        # 10 features: TB, SD, A+%, A%, B%, C%, D%, F%, MTC%, TV
        feature_cols = ["TB", "SD", "A+%", "A%", "B%", "C%", "D%", "F%", "MTC%", "TV"]
        
        # Bổ sung cột thiếu
        for col in feature_cols:
            if col not in sdf.columns:
                sdf = sdf.withColumn(col, F.lit(0.0))
        
        # Cast về double
        for col in feature_cols:
            sdf = sdf.withColumn(col, F.coalesce(F.col(col).cast(DoubleType()), F.lit(0.0)))
        
        # Vector features
        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
        df_vec = assembler.transform(sdf)
        
        # Nếu không có model_path, dùng mặc định
        if not model_path:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "models", "readiness_kmeans_model"
            )
        
        try:
            model = KMeansModel.load(model_path)
            df_clustered = model.transform(df_vec)
        except Exception as e:
            print(f"Không thể tải mô hình học phần từ {model_path}, fitting new: {e}")
            kmeans = KMeans(k=k, seed=seed, featuresCol="features", predictionCol="prediction")
            model = kmeans.fit(df_vec)
            df_clustered = model.transform(df_vec)
        
        # Sắp xếp cluster theo TB (cột 0) - cao TB = chất lượng tốt
        centers = model.clusterCenters()
        cluster_quality = [(i, float(c[0])) for i, c in enumerate(centers)]
        cluster_quality.sort(key=lambda x: x[1], reverse=True)
        
        # Map rank → label (rank 0 = TB cao nhất = Xuất sắc)
        label_by_rank = [
            "Xuất sắc - Tốt",      # rank 0: TB cao nhất
            "Ổn định",             # rank 1: TB khá
            "Không ổn định",       # rank 2: TB thấp
            "Tiêu cực - Kém"       # rank 3: TB thấp nhất
        ]
        
        mapping_expr = F.lit("Chưa xác định")
        for rank, (cluster_id, _) in enumerate(cluster_quality):
            label = label_by_rank[rank] if rank < len(label_by_rank) else "Chưa xác định"
            mapping_expr = F.when(F.col("prediction") == cluster_id, F.lit(label)).otherwise(mapping_expr)
        
        df_clustered = df_clustered.withColumn("ChatLuongCluster", mapping_expr)
        
        return df_clustered.drop("features")


class SubjectQualityPriority:
    """Map label → priority cho UI"""
    PRIORITY_MAP = {
        "Tiêu cực - Kém": 0,
        "Không ổn định": 2,
        "Ổn định": 1,
        "Xuất sắc - Tốt": 3,
    }
    
    @staticmethod
    def get_priority(label):
        return SubjectQualityPriority.PRIORITY_MAP.get(label, 1)
