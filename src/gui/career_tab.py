import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from pyspark.sql import SparkSession

from src.utils.data_utils import load_csv_file
from src.services.career_analyzer import CareerAnalyzerSpark as CareerAnalyzer


class CareerAnalysisTab:
    """
    Class quản lý giao diện và logic Tab xu hướng nghề nghiệp
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame

        # Dữ liệu
        self.df_student = None
        self.df_career_result = None

        # Spark (khởi tạo lazy)
        self.spark = None

        # UI
        self.create_layout()

    # ======================================================
    # SPARK SESSION (AN TOÀN)
    # ======================================================
    def get_spark(self):
        if self.spark is None:
            self.spark = SparkSession.builder \
                .appName("Career Analysis VMU") \
                .master("local[*]") \
                .getOrCreate()
        return self.spark

    # ======================================================
    # UI LAYOUT
    # ======================================================

    def create_layout(self):
        self.paned = tk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(self.paned, bg="#f7f7f7", width=280)
        self.right_frame = tk.Frame(self.paned, bg="white")

        self.paned.add(self.left_frame, minsize=250, width=280)
        self.paned.add(self.right_frame)

        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        content_frame = tk.Frame(self.left_frame, bg="#f7f7f7")
        content_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(content_frame, bg="#f7f7f7", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f7f7f7")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(
            scrollable_frame,
            text="PHÂN TÍCH XU HƯỚNG SINH VIÊN",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 12, "bold"),
            pady=10
        ).pack(fill="x")

        tk.Button(
            scrollable_frame,
            text="📂 TẢI CSV ĐIỂM SINH VIÊN",
            command=self.load_student_csv,
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            pady=8
        ).pack(fill="x", padx=10, pady=10)

        tk.Label(
            scrollable_frame,
            text="🔍 Tìm kiếm (Mã SV / Họ tên):",
            bg="#f7f7f7"
        ).pack(anchor="w", padx=10)

        self.entry_search_sv = tk.Entry(scrollable_frame)
        self.entry_search_sv.pack(fill="x", padx=10, pady=5)

        tk.Button(
            scrollable_frame,
            text="📝 PHÂN TÍCH XU HƯỚNG",
            command=self.analyze_career,
            bg="#8e44ad",
            fg="white",
            font=("Arial", 11, "bold"),
            pady=10
        ).pack(fill="x", padx=10, pady=15)

        tk.Button(
            scrollable_frame,
            text="💾 XUẤT CSV KẾT QUẢ",
            command=self.export_csv,
            bg="#16a085",
            fg="white",
            pady=8
        ).pack(fill="x", padx=10, pady=10)

    def create_right_panel(self):
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill="both", expand=True)

        self.tab_data = tk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="📋 Dữ liệu Sinh viên")

        table_frame = tk.Frame(self.tab_data)
        table_frame.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(table_frame)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            table_frame,
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side=tk.RIGHT, fill="y")
        scroll_x.pack(side=tk.BOTTOM, fill="x")
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)

        self.tab_report = tk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text="📄 Báo cáo Xu hướng")

        self.txt_report = tk.Text(
            self.tab_report,
            font=("Consolas", 11),
            wrap="word"
        )
        self.txt_report.pack(fill="both", expand=True, padx=10, pady=10)

    # ======================================================
    # LOGIC
    # ======================================================

    def load_student_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        try:
            df = load_csv_file(path)
            self.df_student = df.copy()
            self.show_table(df)

            messagebox.showinfo("Thành công", f"Đã tải {len(df)} sinh viên")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def show_table(self, df):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"

        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        for i, (_, row) in enumerate(df.iterrows()):
            if i > 1000:
                break
            self.tree.insert("", "end", values=list(row))

    def analyze_career(self):
        if self.df_student is None:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Vui lòng tải CSV điểm sinh viên trước."
            )
            return

        keyword = self.entry_search_sv.get().strip().lower()

        try:
            spark = self.get_spark()

            # pandas → spark
            spark_df = spark.createDataFrame(self.df_student).cache()

            # Phân tích bằng Spark
            spark_result = CareerAnalyzer.analyze_students(
                spark_df,
                keyword
            )

            if spark_result is None or spark_result.count() == 0:
                messagebox.showinfo(
                    "Không có dữ liệu",
                    "Không tìm thấy sinh viên phù hợp."
                )
                return

            # spark → pandas
            result_df = spark_result.toPandas()
            self.df_career_result = result_df

            # Hiển thị bảng
            self.show_table(result_df)

            # =============================
            # SINH BÁO CÁO CHI TIẾT
            # =============================
            self.txt_report.delete(1.0, tk.END)
            self.notebook.select(self.tab_report)

            self.txt_report.insert(
                tk.END,
                f"ĐÃ PHÂN TÍCH {len(result_df)} SINH VIÊN\n\n"
            )

            for idx, row in result_df.iterrows():
                ma_sv = row.get("ma_sv", "")
                ho_ten = row.get("ho_ten", "")
                nganh = row.get("nganh_phu_hop", "")

                self.txt_report.insert(tk.END, f"SINH VIÊN {idx + 1}\n")
                self.txt_report.insert(tk.END, f"Mã sinh viên : {ma_sv}\n")
                self.txt_report.insert(tk.END, f"Họ và tên    : {ho_ten}\n\n")

                self.txt_report.insert(
                    tk.END,
                    "• Kết quả phân tích học tập:\n"
                    "- Điểm trung bình các môn chuyên ngành phản ánh rõ xu hướng học tập.\n\n"
                )

                self.txt_report.insert(
                    tk.END,
                    "• Định hướng nghề nghiệp đề xuất:\n"
                    f"→ Ngành phù hợp: {nganh}\n\n"
                )

                self.txt_report.insert(
                    tk.END,
                    "-" * 60 + "\n\n"
                )

            messagebox.showinfo(
                "Hoàn tất",
                f"Đã phân tích và tạo báo cáo cho {len(result_df)} sinh viên."
            )

        except Exception as e:
            messagebox.showerror("Lỗi Phân Tích", str(e))

    def export_csv(self):
        if self.df_career_result is None:
            messagebox.showwarning("Chưa có dữ liệu", "Chưa có kết quả.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="xu_huong_nghe_nghiep_sinh_vien.csv"
        )

        if path:
            try:
                self.df_career_result.to_csv(path, index=False, encoding="utf-8-sig")
                messagebox.showinfo("Hoàn tất", "Đã xuất file CSV.")
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))
