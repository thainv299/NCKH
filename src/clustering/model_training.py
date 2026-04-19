from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans

def train_model(features, k=4):
    """
    Train KMeans model với số cụm K có thể tùy chỉnh
    """
    assembler = VectorAssembler(
        inputCols=["gpa", "std_score", "failed_subjects", "excellent_subjects"],
        outputCol="features"
    )

    data = assembler.transform(features)

    print(f"🔄 Training KMeans with K={k}...")
    kmeans = KMeans(k=k, seed=1)
    model = kmeans.fit(data)

    # Save model
    model_path = "models/kmeans_model"
    model.write().overwrite().save(model_path)
    print(f"💾 Model saved to {model_path}")

    return model, data