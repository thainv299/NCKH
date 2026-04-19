from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import VectorAssembler
from src.ml.unsupervised.evaluate_kmeans import evaluate_optimal_k

def evaluate_optimal_k_for_data(data, min_k=2, max_k=8, seed=42, feature_cols=None, auto_select=True):
    """
    Đánh giá số lượng cụm K tối ưu cho dataset
    Tự động vectorize nếu chưa có cột features
    """
    print("🔍 Đánh giá số lượng cụm K tối ưu...")

    # Kiểm tra xem đã có cột features chưa
    if "features" not in data.columns:
        # Nếu chưa có, tự động vectorize
        if feature_cols is None:
            # Auto-detect feature columns (loại bỏ các cột không phải feature)
            exclude_cols = ["ma_sv", "prediction", "cluster"]
            feature_cols = [col for col in data.columns if col not in exclude_cols]

        print(f"⚙️ Vectorizing features: {feature_cols}")
        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
        data = assembler.transform(data)

    optimal_k, results = evaluate_optimal_k(data, min_k=min_k, max_k=max_k, seed=seed, auto_select=auto_select)

    return optimal_k

def evaluate(model, data):
    """
    Đánh giá model đã train với Silhouette Score
    """
    clusters = model.transform(data)

    evaluator = ClusteringEvaluator()
    silhouette = evaluator.evaluate(clusters)

    print(f"✅ Silhouette Score của model: {silhouette:.4f}")

    # Phân tích chất lượng clustering
    if silhouette > 0.7:
        print("🎉 Clustering chất lượng RẤT TỐT")
    elif silhouette > 0.5:
        print("👍 Clustering chất lượng TỐT")
    elif silhouette > 0.25:
        print("⚠️ Clustering chất lượng TRUNG BÌNH")
    else:
        print("❌ Clustering chất lượng KÉM - cân nhắc điều chỉnh K")

    return clusters