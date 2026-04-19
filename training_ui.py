"""
Giao diện huấn luyện mô hình - Cấu hình và thực thi các tiến trình huấn luyện mô hình phân cụm.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Cấu hình đường dẫn gốc của dự án để hỗ trợ nạp các module liên quan.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Import các module chức năng xử lý dữ liệu và thuật toán huấn luyện.
from src.clustering.load_data import load_data
from src.clustering.transform import transform_to_fact
from src.clustering.feature_engineering import create_features
from src.clustering.model_training import train_model
from src.clustering.evaluation import evaluate_optimal_k_for_data

from src.ml.unsupervised.train_readiness import train_readiness_model
from src.ml.unsupervised.train_readiness_subjects import train_subject_quality_model
from src.ml.unsupervised.evaluate_kmeans import evaluate_optimal_k

from pyspark.sql import SparkSession

class TrainingUI:
    """
    Lớp quản lý giao diện hỗ trợ thiết lập tham số và chạy các tiến trình huấn luyện.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Cấu hình Huấn luyện Mô hình")
        self.root.geometry("1000x700")

        # Các biến điều khiển lưu trữ trạng thái lựa chọn trên giao diện.
        self.training_type = tk.StringVar(value="student_analysis")
        self.data_file = tk.StringVar()
        self.k_value = tk.StringVar(value="4")
        self.output_path = tk.StringVar(value="models/")

        self.spark = None

        self.setup_ui()

    def setup_ui(self):
        """Khởi tạo cấu trúc giao diện người dùng."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Hệ thống Huấn luyện Mô hình",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Lựa chọn loại mô hình cần huấn luyện.
        type_frame = ttk.LabelFrame(main_frame, text="Cấu hình huấn luyện", padding="10")
        type_frame.pack(fill=tk.X, pady=5)

        ttk.Label(type_frame, text="Phân loại:").grid(row=0, column=0, sticky=tk.W, pady=5)
        training_types = {
            "student_analysis": "Phân tích điểm sinh viên (Student Analysis)",
            "career_readiness": "Đánh giá sẵn sàng nghề nghiệp (Career Readiness)",
            "subject_quality": "Phân tích chất lượng môn học (Subject Quality)"
        }

        type_combo = ttk.Combobox(type_frame, textvariable=self.training_type,
                                 values=list(training_types.values()), state="readonly", width=50)
        type_combo.grid(row=0, column=1, padx=10, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self.on_training_type_change)

        # Lựa chọn nguồn dữ liệu đầu vào.
        data_frame = ttk.LabelFrame(main_frame, text="Dữ liệu đầu vào", padding="10")
        data_frame.pack(fill=tk.X, pady=5)

        ttk.Label(data_frame, text="Đường dẫn:").grid(row=0, column=0, sticky=tk.W, pady=5)
        data_entry = ttk.Entry(data_frame, textvariable=self.data_file, width=50)
        data_entry.grid(row=0, column=1, padx=10, pady=5)

        browse_btn = ttk.Button(data_frame, text="Duyệt file...", command=self.browse_data_file)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # Cấu hình tham số mô hình và trực quan hóa kết quả đánh giá.
        k_frame = ttk.LabelFrame(main_frame, text="Tham số K và Đánh giá", padding="10")
        k_frame.pack(fill=tk.X, pady=5)

        ttk.Label(k_frame, text="Số cụm (K):").grid(row=0, column=0, sticky=tk.W, pady=5)
        k_entry = ttk.Entry(k_frame, textvariable=self.k_value, width=10)
        k_entry.grid(row=0, column=1, padx=10, pady=5)

        chart_btn = ttk.Button(k_frame, text="Xem đồ thị Silhouette & Elbow",
                              command=self.show_evaluation_charts)
        chart_btn.grid(row=0, column=2, padx=10, pady=5)

        # Thiết lập đường dẫn lưu trữ mô hình đầu ra.
        output_frame = ttk.LabelFrame(main_frame, text="Lưu trữ mô hình", padding="10")
        output_frame.pack(fill=tk.X, pady=5)

        ttk.Label(output_frame, text="Thư mục lưu:").grid(row=0, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=50)
        output_entry.grid(row=0, column=1, padx=10, pady=5)

        browse_output_btn = ttk.Button(output_frame, text="Chọn thư mục...",
                                      command=self.browse_output_path)
        browse_output_btn.grid(row=0, column=2, padx=5, pady=5)

        # Thực thi tiến trình huấn luyện.
        train_frame = ttk.Frame(main_frame)
        train_frame.pack(fill=tk.X, pady=20)

        train_btn = ttk.Button(train_frame, text="Bắt đầu Huấn luyện",
                              command=self.train_model, style="Accent.TButton")
        train_btn.pack(pady=10)

        # Hiển thị trạng thái của tiến trình.
        self.status_label = ttk.Label(main_frame, text="Sẵn sàng", foreground="blue")
        self.status_label.pack(pady=5)

        self.set_default_data_files()

    def on_training_type_change(self, event=None):
        """Cập nhật đường dẫn tệp tin tương ứng khi thay đổi loại huấn luyện."""
        self.set_default_data_files()

    def set_default_data_files(self):
        """Thiết lập các tệp dữ liệu mặc định dựa trên loại huấn luyện đã chọn."""
        training_type = self.training_type.get()

        if "Student Analysis" in training_type:
            self.data_file.set("data/data_demo.csv")
        elif "Career Readiness" in training_type:
            self.data_file.set("data/data_demo_1.csv")
        elif "Subject Quality" in training_type:
            self.data_file.set("data/Thongke.Csv")

    def browse_data_file(self):
        """Mở hộp thoại chọn tệp dữ liệu đầu vào."""
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Chọn tệp dữ liệu",
                                            filetypes=filetypes,
                                            initialdir=os.path.join(project_root, "data"))
        if filename:
            if filename.startswith(project_root):
                self.data_file.set(os.path.relpath(filename, project_root))
            else:
                self.data_file.set(filename)

    def browse_output_path(self):
        """Mở hộp thoại lựa chọn thư mục lưu trữ mô hình."""
        dirname = filedialog.askdirectory(title="Chọn thư mục lưu mô hình",
                                        initialdir=os.path.join(project_root, "models"))
        if dirname:
            if dirname.startswith(project_root):
                self.output_path.set(os.path.relpath(dirname, project_root))
            else:
                self.output_path.set(dirname)

    def show_evaluation_charts(self):
        """Hiển thị các biểu đồ hỗ trợ đánh giá và lựa chọn số cụm K tối ưu."""
        try:
            self.status_label.config(text="Đang xử lý dữ liệu và đánh giá...", foreground="orange")
            self.root.update()

            data = self.load_data_for_evaluation()

            if data is None:
                return

            optimal_k, results = evaluate_optimal_k(data, min_k=2, max_k=8, seed=42, auto_select=False)

            chart_window = tk.Toplevel(self.root)
            chart_window.title("Phân tích tham số K tối ưu")
            chart_window.geometry("1200x600")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Biểu đồ Silhouette Score.
            k_values = list(results.keys())
            silhouette_scores = [results[k]['silhouette'] for k in k_values]
            ax1.plot(k_values, silhouette_scores, 'bo-', linewidth=2, markersize=8)
            ax1.set_title(' Silhouette Score theo K')
            ax1.set_xlabel('Số cụm (K)')
            ax1.set_ylabel('Silhouette Score')
            ax1.grid(True, alpha=0.3)

            optimal_idx = k_values.index(optimal_k)
            ax1.plot(optimal_k, silhouette_scores[optimal_idx], 'ro', markersize=12, label=f'K tối ưu: {optimal_k}')
            ax1.legend()

            # Biểu đồ WCSS (Elbow Method).
            wcss_values = [results[k]['wcss'] for k in k_values]
            ax2.plot(k_values, wcss_values, 'go-', linewidth=2, markersize=8)
            ax2.set_title('WCSS ( Elbow Method) theo K')
            ax2.set_xlabel('Số cụm (K)')
            ax2.set_ylabel('Tổng bình phương sai số')
            ax2.grid(True, alpha=0.3)

            ax2.plot(optimal_k, wcss_values[optimal_idx], 'ro', markersize=12, label=f'Điểm Elbow: K = {optimal_k}')
            ax2.legend()

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.k_value.set(str(optimal_k))
            self.status_label.config(text=f"Hoàn tất đánh giá. K tối ưu gợi ý: {optimal_k}", foreground="green")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị đồ thị đánh giá: {str(e)}")
            self.status_label.config(text="Lỗi hiển thị", foreground="red")

    def load_data_for_evaluation(self):
        """Tải và chuẩn bị dữ liệu cho tiến trình đánh giá mô hình."""
        data_file = self.data_file.get()
        if not data_file:
            messagebox.showerror("Lỗi", "Chưa chọn dữ liệu đầu vào")
            return None

        if not os.path.isabs(data_file):
            data_file = os.path.join(project_root, data_file)

        if not os.path.exists(data_file):
            messagebox.showerror("Lỗi", f"Không tìm thấy tệp tin: {data_file}")
            return None

        try:
            if self.spark is None:
                self.spark = SparkSession.builder \
                    .appName("TrainingUI") \
                    .getOrCreate()

            training_type = self.training_type.get()

            if "Student Analysis" in training_type:
                spark, df = load_data(data_file.replace(project_root + os.sep, ""))
                fact_score = transform_to_fact(df)
                features = create_features(fact_score)
                feature_cols = ["gpa", "std_score", "failed_subjects", "excellent_subjects"]

                from pyspark.ml.feature import VectorAssembler
                assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
                return assembler.transform(features)

            elif "Career Readiness" in training_type:
                df = self.spark.read.csv(data_file, header=True, inferSchema=True, sep=";")
                from src.services.career_analyzer import CareerAnalyzerSpark
                df = CareerAnalyzerSpark.compute_field_gpa(df)

                from pyspark.sql import functions as F
                from pyspark.sql.types import DoubleType
                feature_cols = ["gpa_tong", "TOEIC"]

                if "TOEIC" not in df.columns:
                    df = df.withColumn("TOEIC", F.lit(0.0))

                for c in feature_cols:
                    df = df.withColumn(c, F.coalesce(F.col(c).cast(DoubleType()), F.lit(0.0)))

                assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
                return assembler.transform(df)

            elif "Subject Quality" in training_type:
                df = self.spark.read \
                    .option("header", True) \
                    .option("inferSchema", True) \
                    .option("delimiter", ",") \
                    .csv(data_file)

                feature_cols = ["TB", "SD", "A+%", "A%", "B%", "C%", "D%", "F%", "MTC%", "TV"]

                assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
                return assembler.transform(df)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nạp dữ liệu: {str(e)}")
            return None

    def train_model(self):
        """Thực hiện quá trình huấn luyện mô hình dựa trên các cấu hình hiện tại."""
        try:
            self.status_label.config(text="Đang thực hiện huấn luyện mô hình...", foreground="orange")
            self.root.update()

            training_type = self.training_type.get()
            data_file = self.data_file.get()
            k = int(self.k_value.get())
            output_path = self.output_path.get()

            if not data_file:
                messagebox.showerror("Lỗi", "Yêu cầu chọn dữ liệu đầu vào")
                return

            if not output_path:
                messagebox.showerror("Lỗi", "Yêu cầu chọn đường dẫn lưu mô hình")
                return

            if not os.path.isabs(data_file):
                data_file = os.path.join(project_root, data_file)
            if not os.path.isabs(output_path):
                output_path = os.path.join(project_root, output_path)

            os.makedirs(output_path, exist_ok=True)

            if "Student Analysis" in training_type:
                self.train_student_analysis(data_file, k, output_path)
            elif "Career Readiness" in training_type:
                self.train_career_readiness(data_file, k, output_path)
            elif "Subject Quality" in training_type:
                self.train_subject_quality(data_file, k, output_path)

            self.status_label.config(text="Huấn luyện mô hình hoàn tất", foreground="green")
            messagebox.showinfo("Thông báo", "Quá trình huấn luyện đã kết thúc thành công.")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi thực thi huấn luyện: {str(e)}")
            self.status_label.config(text="Thất bại", foreground="red")

    def train_student_analysis(self, data_file, k, output_path):
        """Tiến trình huấn luyện mô hình phân tích sinh viên."""
        spark, df = load_data(data_file.replace(project_root + os.sep, ""))
        fact_score = transform_to_fact(df)
        features = create_features(fact_score)
        model, data = train_model(features, k=k)

        model_path = os.path.join(output_path, "student_analysis_kmeans_model")
        model.write().overwrite().save(model_path)

    def train_career_readiness(self, data_file, k, output_path):
        """Tiến trình huấn luyện mô hình đánh giá sẵn sàng nghề nghiệp."""
        spark = SparkSession.builder.appName("TrainCareerReadiness").getOrCreate()
        df = spark.read.csv(data_file, header=True, inferSchema=True, sep=";")

        from src.services.career_analyzer import CareerAnalyzerSpark
        from pyspark.sql import functions as F
        from pyspark.sql.types import DoubleType
        from pyspark.ml.feature import VectorAssembler
        from pyspark.ml.clustering import KMeans

        df = CareerAnalyzerSpark.compute_field_gpa(df)

        feature_cols = ["gpa_tong", "TOEIC"]
        if "TOEIC" not in df.columns:
            df = df.withColumn("TOEIC", F.lit(0.0))

        for c in feature_cols:
            df = df.withColumn(c, F.coalesce(F.col(c).cast(DoubleType()), F.lit(0.0)))

        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
        df_vec = assembler.transform(df)

        kmeans = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster")
        model = kmeans.fit(df_vec)

        model_path = os.path.join(output_path, "career_readiness_kmeans_model")
        model.write().overwrite().save(model_path)

    def train_subject_quality(self, data_file, k, output_path):
        """Tiến trình huấn luyện mô hình chất lượng môn học."""
        spark = SparkSession.builder.appName("TrainSubjectQuality").getOrCreate()
        df = spark.read \
            .option("header", True) \
            .option("inferSchema", True) \
            .option("delimiter", ",") \
            .csv(data_file)

        model, data = train_subject_quality_model(df, k=k, evaluate_model=False)

        model_path = os.path.join(output_path, "subject_quality_kmeans_model")
        model.write().overwrite().save(model_path)


def main():
    """Hàm khởi động chương trình."""
    root = tk.Tk()
    app = TrainingUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()