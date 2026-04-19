from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.sql import SparkSession
from src.ml.unsupervised.evaluate_kmeans import evaluate_optimal_k


def train_subject_quality_model(features_df, k=4, seed=42, evaluate_model=True):
    feature_cols = ["TB", "SD", "A+%", "A%", "B%", "C%", "D%", "F%", "MTC%", "TV"]

    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    data = assembler.transform(features_df)

    # Đánh giá model nếu được yêu cầu (chỉ mang tính chất tham khảo đồ thị)
    if evaluate_model:
        print("\nEvaluating optimal number of clusters K...")
        evaluate_optimal_k(data, min_k=2, max_k=8, seed=seed, auto_select=True)
        # Tuyệt đối không ghi đè k để đảm bảo nhất quán với 4 mức độ của hệ thống

    kmeans = KMeans(k=k, seed=seed, featuresCol="features", predictionCol="prediction")
    model = kmeans.fit(data)

    return model, data


if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("Train Subject Quality Model") \
        .master("local[*]") \
        .getOrCreate()
    
    try:
        sdf = spark.read \
            .option("header", True) \
            .option("inferSchema", True) \
            .option("delimiter", ",") \
            .csv("data/Thongke.Csv")
        
        print(f"Loaded {sdf.count()} subjects")
        print(f"Columns: {sdf.columns}")
        
        model, data = train_subject_quality_model(sdf, k=4, evaluate_model=True)
        
        # Bổ sung lệnh lưu mô hình để tránh việc mô hình bị xóa sau khi Spark dừng
        model_path = "models/readiness_kmeans_model"
        model.write().overwrite().save(model_path)
        
        print(f"\n✓ Model saved to {model_path}")
        print(f"Cluster centers:\n{model.clusterCenters()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        spark.stop()
