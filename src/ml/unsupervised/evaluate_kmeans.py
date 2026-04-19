import matplotlib.pyplot as plt
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

def evaluate_optimal_k(dataset, min_k=2, max_k=10, seed=42):
    """
    Hàm đánh giá và tìm kiếm số lượng cụm K tối ưu cho thuật toán KMeans.
    
    Yêu cầu: 
    - dataset: Spark DataFrame đã qua bước VectorAssembler (dữ liệu gom vào cột 'features').
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

    # 4. Trực quan hóa dữ liệu (Biểu đồ trục kép)
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Trục Y thứ nhất (WCSS - Đường màu đỏ)
    ax1.set_xlabel('Số lượng cụm (K)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('WCSS (Training Cost)', color='tab:red', fontsize=12, fontweight='bold')
    ax1.plot(k_values, wcss_costs, marker='o', color='tab:red', linewidth=2, label='WCSS (Elbow)')
    ax1.tick_params(axis='y', labelcolor='tab:red')

    # Trục Y thứ hai (Silhouette - Đường nét đứt màu xanh)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Hệ số Silhouette', color='tab:blue', fontsize=12, fontweight='bold')
    ax2.plot(k_values, silhouette_scores, marker='s', color='tab:blue', linewidth=2, linestyle='dashed', label='Silhouette')
    ax2.tick_params(axis='y', labelcolor='tab:blue')

    # Định dạng đồ thị
    plt.title('Đánh giá Mô hình KMeans: Phương pháp Khuỷu tay & Hệ số Silhouette', fontsize=14, pad=15)
    fig.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Hiển thị
    plt.show()