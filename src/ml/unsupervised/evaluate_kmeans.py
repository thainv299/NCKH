import matplotlib.pyplot as plt
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

def evaluate_optimal_k(dataset, min_k=2, max_k=10, seed=42, auto_select=True):
    """
    Hàm đánh giá và tìm kiếm số lượng cụm K tối ưu cho thuật toán KMeans.

    Args:
        dataset: Spark DataFrame đã qua bước VectorAssembler (dữ liệu gom vào cột 'features')
        min_k: Số cụm tối thiểu để test
        max_k: Số cụm tối đa để test
        seed: Random seed
        auto_select: Có tự động chọn K hay không

    Returns:
        optimal_k: Số cụm được chọn
        results: Dict chứa tất cả metrics
    """
    wcss_costs = []
    silhouette_scores = []
    k_values = range(min_k, max_k + 1)

    # Khởi tạo công cụ đánh giá Silhouette
    evaluator = ClusteringEvaluator(
        predictionCol="prediction",
        featuresCol="features",
        metricName="silhouette",
        distanceMeasure="squaredEuclidean"
    )

    print(f"{'K':<5} | {'WCSS (Training Cost)':<25} | {'Silhouette Score':<20}")
    print("-" * 55)

    for k in k_values:
        # 1. Khởi tạo và huấn luyện mô hình
        kmeans = KMeans(k=k, seed=seed, featuresCol="features", predictionCol="prediction")
        model = kmeans.fit(dataset)

        # 2. Trích xuất WCSS (Hàm mục tiêu)
        cost = model.summary.trainingCost
        wcss_costs.append(cost)

        # 3. Tính toán Hệ số Silhouette
        predictions = model.transform(dataset)
        silhouette = evaluator.evaluate(predictions)
        silhouette_scores.append(silhouette)

        print(f"{k:<5} | {cost:<25.4f} | {silhouette:<20.4f}")

    # Tự động chọn K tối ưu
    if auto_select:
        optimal_k = select_optimal_k(k_values, wcss_costs, silhouette_scores)
        print(f"\nAUTO-SELECTED: K={optimal_k} (based on multi-criteria analysis)")
    else:
        optimal_k = k_values[len(k_values)//2]  # Default: K ở giữa
        print(f"\n💡 GỠI Ý XEM BIỂU ĐỒ: K={optimal_k} (có thể điều chỉnh)")


    # Trả về kết quả
    results = {
        'k_values': list(k_values),
        'wcss_costs': wcss_costs,
        'silhouette_scores': silhouette_scores,
        'optimal_k': optimal_k
    }

    return optimal_k, results

def select_optimal_k(k_values, wcss_costs, silhouette_scores):
    """
    Tự động chọn K tối ưu dựa trên multiple criteria
    """
    # 1. Tìm K có Silhouette Score cao nhất
    best_silhouette_k = k_values[silhouette_scores.index(max(silhouette_scores))]

    # 2. Tìm Elbow point (điểm khuỷu) - nơi WCSS giảm chậm nhất
    elbow_k = find_elbow_point(k_values, wcss_costs)

    # 3. Tính điểm tổng hợp cho mỗi K
    scores = []
    for i, k in enumerate(k_values):
        sil_score = silhouette_scores[i] * 100  # Scale lên 0-100
        wcss_score = (max(wcss_costs) - wcss_costs[i]) / (max(wcss_costs) - min(wcss_costs)) * 100  # Normalize

        # Công thức: 70% Silhouette + 30% WCSS reduction
        total_score = 0.7 * sil_score + 0.3 * wcss_score
        scores.append(total_score)

    # K có điểm cao nhất
    best_combined_k = k_values[scores.index(max(scores))]

    print("📊 Phân tích tự động chọn K:")
    print(f"   • K cao Silhouette nhất: {best_silhouette_k} (score: {max(silhouette_scores):.4f})")
    print(f"   • K tại Elbow point: {elbow_k}")
    print(f"   • K cân bằng tốt nhất: {best_combined_k} (score: {max(scores):.1f})")

    # Ưu tiên: Best combined > Best silhouette > Elbow
    if best_combined_k in [best_silhouette_k, elbow_k]:
        return best_combined_k
    else:
        return best_silhouette_k  # Fallback to silhouette

def find_elbow_point(k_values, wcss_costs):
    """
    Tìm điểm khuỷu (elbow point) trong WCSS curve
    """
    # Tính độ dốc (slope) giữa các điểm
    slopes = []
    for i in range(1, len(wcss_costs)):
        slope = wcss_costs[i-1] - wcss_costs[i]
        slopes.append(slope)

    # Tìm điểm có độ dốc thay đổi nhiều nhất
    slope_changes = []
    for i in range(1, len(slopes)):
        change = slopes[i-1] - slopes[i]
        slope_changes.append(change)

    # Elbow point là điểm có slope change lớn nhất
    if slope_changes:
        elbow_idx = slope_changes.index(max(slope_changes)) + 1
        return k_values[elbow_idx]
    else:
        return k_values[len(k_values)//2]  # Fallback