import os
import sys

# Thêm path cha để python hiểu module src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
from src.services.career_analyzer import CareerAnalyzerSpark

def train_readiness_model():
    print("Khởi tạo Spark Session...")
    spark = SparkSession.builder \
        .appName("TrainReadinessModel") \
        .getOrCreate()
        
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "input", "data_demo_1.csv")
    
    print(f"Đang đọc dữ liệu từ: {csv_path}")
    df = spark.read.csv(csv_path, header=True, inferSchema=True, sep=";")
    
    # Kế thừa hàm tính gpa của CareerAnalyzerSpark
    print("Tính toán GPA theo chuẩn...")
    df = CareerAnalyzerSpark.compute_field_gpa(df)
    
    # Feature engineering: ["gpa_tong", "TOEIC"]
    feature_cols = ["gpa_tong", "TOEIC"]
    
    # Coalesce (điền 0 nếu null hoặc missing type)
    if "TOEIC" not in df.columns:
        df = df.withColumn("TOEIC", F.lit(0.0))
        
    for c in feature_cols:
        df = df.withColumn(c, F.coalesce(F.col(c).cast(DoubleType()), F.lit(0.0)))
        
    print("Vectorizing...")
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    df_vec = assembler.transform(df)
    
    # Train KMeans (k=3)
    k = 3
    print(f"Đang huấn luyện mô hình K-Means (k={k}) để thiết lập chuẩn đánh giá Tuyệt đối...")
    kmeans = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster")
    model = kmeans.fit(df_vec)
    
    # Preview Centers
    centers = model.clusterCenters()
    print("Toạ độ tâm cụm (gpa_tong, TOEIC):")
    for i, c in enumerate(centers):
        print(f"  Cluster {i}: GPA {c[0]:.2f}, TOEIC {c[1] if len(c)>1 else 0:.0f}")

    # Save
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "readiness_kmeans_model")
    model.write().overwrite().save(out_path)
    print(f"✅ Đã lưu mô hình chuẩn tại: {out_path}")
    
if __name__ == "__main__":
    train_readiness_model()
