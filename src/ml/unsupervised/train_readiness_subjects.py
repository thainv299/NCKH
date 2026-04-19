from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.sql import SparkSession


def train_subject_quality_model(features_df, k=4, seed=42):
    feature_cols = ["TB", "SD", "A+%", "A%", "B%", "C%", "D%", "F%", "MTC%", "TV"]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    data = assembler.transform(features_df)
    
    kmeans = KMeans(k=k, seed=seed, featuresCol="features", predictionCol="prediction")
    model = kmeans.fit(data)
    
    model.write().overwrite().save("models/readiness_kmeans_model")
    
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
        
        model, data = train_subject_quality_model(sdf)
        
        print("\n✓ Model saved to models/readiness_kmeans_model/")
        print(f"Cluster centers:\n{model.clusterCenters()}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        spark.stop()
