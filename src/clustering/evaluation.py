from pyspark.ml.evaluation import ClusteringEvaluator

def evaluate(model, data):

    clusters = model.transform(data)

    evaluator = ClusteringEvaluator()
    silhouette = evaluator.evaluate(clusters)

    print("Silhouette Score:", silhouette)

    return clusters