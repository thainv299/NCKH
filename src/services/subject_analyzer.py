"""
Xử lý logic phân tích học phần
"""
from pyspark.sql.functions import col, when

class SubjectAnalyzer:
    """
    Class xử lý phân tích học phần bằng Spark
    """
    
    @staticmethod
    def analyze_subjects(sdf, selected_codes):
        """
        sdf: Spark DataFrame
        selected_codes: list mã môn
        """

        # Lọc bằng Spark (KHÔNG dùng pandas nữa)
        sdf = sdf.filter(col("MaMH").isin(selected_codes))

        # Ép kiểu số (quan trọng)
        numeric_cols = ["TB", "F%", "SD", "A%", "A+%"]
        for c in numeric_cols:
            if c in sdf.columns:
                sdf = sdf.withColumn(c, col(c).cast("double"))

        # 1. Độ khó
        sdf = sdf.withColumn(
            "DoKho",
            when((col("TB") < 6.0) | (col("F%") > 15), "Khó")
            .when(col("TB") >= 8.0, "Dễ")
            .otherwise("Trung bình")
        )

        # 2. Chất lượng
        if "SD" in sdf.columns and "A%" in sdf.columns and "A+%" in sdf.columns:
            sdf = sdf.withColumn(
                "ChatLuong",
                when((col("SD") > 1.0) & (col("F%") > 10),
                     "Không ổn định / Cần cải thiện")
                .when((col("A%") + col("A+%") > 40) & (col("SD") < 0.7),
                      "Tốt & đồng đều")
                .otherwise("Ổn định")
            )
        else:
            sdf = sdf.withColumn(
                "ChatLuong",
                when(col("MaMH").isNotNull(),
                     "Không đủ dữ liệu đánh giá")
            )

        # 3. Xu hướng
        sdf = sdf.withColumn(
            "XuHuong",
            when(col("TB") >= 7.5, "Tích cực")
            .when(col("TB") < 5.0, "Tiêu cực")
            .otherwise("Bình thường")
        )

        return sdf.select(
            "MaMH", "TenMH", "DoKho",
            "ChatLuong", "XuHuong", "TB", "F%"
        )
    
    @staticmethod
    def generate_report_text(results, options):
        """
        Tạo nội dung báo cáo dạng text
        
        Args:
            results: List kết quả từ Spark
            options: Dict các tùy chọn hiển thị
            
        Returns:
            List các dòng text để hiển thị
        """
        report_lines = []
        
        for row in results:
            mon_hoc = f"{row['TenMH']} ({row['MaMH']})"
            
            report_lines.append({
                "text": f"Nội dung phân tích {mon_hoc}:\n",
                "tag": "header"
            })
            
            # 1. Độ khó
            if options.get("dokho", True):
                report_lines.append({
                    "text": "1. Độ khó của học phần:\n",
                    "tag": "subheader"
                })
                msg = (
                    f"- Đánh giá: {row['DoKho']} "
                    f"(Điểm TB: {row['TB']}, Tỷ lệ rớt: {row['F%']}%)\n"
                )
                report_lines.append({"text": msg, "tag": "content"})
            
            # 2. Chất lượng
            if options.get("chatluong", True):
                report_lines.append({
                    "text": "2. Chất lượng giảng dạy:\n",
                    "tag": "subheader"
                })
                msg = f"- Đánh giá: {row['ChatLuong']}\n"
                report_lines.append({"text": msg, "tag": "content"})
            
            # 3. Xu hướng
            if options.get("xuhuong", True):
                report_lines.append({
                    "text": "3. Xu hướng học tập chung của sinh viên:\n",
                    "tag": "subheader"
                })
                msg = f"- Đánh giá: {row['XuHuong']}\n"
                report_lines.append({"text": msg, "tag": "content"})
            
            report_lines.append({"text": "\n" + "-" * 40 + "\n\n", "tag": "divider"})
        
        return report_lines

    @staticmethod
    def analyze_all_subjects(sdf):

        numeric_cols = ["TB", "F%", "SD", "A%", "A+%"]
        for c in numeric_cols:
            if c in sdf.columns:
                sdf = sdf.withColumn(c, col(c).cast("double"))

        # Độ khó
        sdf = sdf.withColumn(
            "DoKho",
            when((col("TB") < 6.0) | (col("F%") > 15), "Khó")
            .when(col("TB") >= 8.0, "Dễ")
            .otherwise("Trung bình")
        )

        # Chất lượng
        if "SD" in sdf.columns and "A%" in sdf.columns and "A+%" in sdf.columns:
            sdf = sdf.withColumn(
                "ChatLuong",
                when((col("SD") > 1.0) & (col("F%") > 10),
                    "Không ổn định / Cần cải thiện")
                .when((col("A%") + col("A+%") > 40) & (col("SD") < 0.7),
                    "Tốt & đồng đều")
                .otherwise("Ổn định")
            )
        else:
            sdf = sdf.withColumn(
                "ChatLuong",
                when(col("MaMH").isNotNull(),
                    "Không đủ dữ liệu đánh giá")
            )

        # Xu hướng
        sdf = sdf.withColumn(
            "XuHuong",
            when(col("TB") >= 7.5, "Tích cực")
            .when(col("TB") < 5.0, "Tiêu cực")
            .otherwise("Bình thường")
        )

        return sdf.select(
            "MaMH", "TenMH",
            "DoKho", "ChatLuong",
            "XuHuong", "TB", "F%"
        )
