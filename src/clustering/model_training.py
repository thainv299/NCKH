from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans

def train_model(features):
    assembler = VectorAssembler(
        inputCols=["gpa", "std_score", "failed_subjects", "excellent_subjects"],
        outputCol="features"
    )
    
    data = assembler.transform(features)

    kmeans = KMeans(k=4, seed=1)
    model = kmeans.fit(data)
    model.write().overwrite().save("models/kmeans_model")
    return model, data