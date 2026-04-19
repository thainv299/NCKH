"""
Tab đánh giá mức độ sẵn sàng nghề nghiệp
GPA theo nhóm môn → Đối sánh thị trường → KMeans phân cụm
"""
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from pyspark.sql import SparkSession

from src.utils.data_utils import load_csv_file
from src.services.career_analyzer import CareerAnalyzerSpark as CareerAnalyzer


class CareerAnalysisTab:
    """
    Tab danh gia muc do san sang nghe nghiep
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame

        # Du lieu
        self.spark_df = None
        self.df_career_result = None
        self.market_data = None
        self.important_subjects = None

        # Spark
        self.spark = None
        self.model_path = tk.StringVar(value="models/career_readiness_kmeans_model")

        # UI
        self.create_layout()

    # ======================================================
    # SPARK SESSION
    # ======================================================
    def get_spark(self):
        if self.spark is None:
            self.spark = SparkSession.builder \
                .appName("Career Readiness VMU") \
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

        # === HEADER ===
        tk.Label(
            scrollable_frame,
            text="DANH GIA SAN SANG NGHE NGHIEP",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 11, "bold"),
            pady=10
        ).pack(fill="x")

        # === NUT TAI CSV ===
        tk.Button(
            scrollable_frame,
            text="TAI CSV DIEM SINH VIEN",
            command=self.load_student_csv,
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            pady=8
        ).pack(fill="x", padx=10, pady=10)

        # === TIM KIEM ===
        tk.Label(
            scrollable_frame,
            text="Tim kiem (Ma SV / Ho ten):",
            bg="#f7f7f7"
        ).pack(anchor="w", padx=10)

        self.entry_search_sv = tk.Entry(scrollable_frame)
        self.entry_search_sv.pack(fill="x", padx=10, pady=5)

        # === NUT DANH GIA ===
        tk.Button(
            scrollable_frame,
            text="DANH GIA SAN SANG",
            command=self.analyze_career,
            bg="#8e44ad",
            fg="white",
            font=("Arial", 11, "bold"),
            pady=10
        ).pack(fill="x", padx=10, pady=15)

        # === CHON MODEL ===
        tk.Label(
            scrollable_frame,
            text="Mo hinh huan luyen:",
            bg="#f7f7f7",
            font=("Arial", 9, "bold")
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        model_f = tk.Frame(scrollable_frame, bg="#f7f7f7")
        model_f.pack(fill="x", padx=10, pady=2)
        
        tk.Entry(model_f, textvariable=self.model_path, font=("Arial", 9)).pack(side="left", fill="x", expand=True)
        tk.Button(model_f, text="...", command=self.browse_model, width=3, font=("Arial", 9)).pack(side="left", padx=2)

        # === NUT XUAT CSV ===
        tk.Button(
            scrollable_frame,
            text="XUAT CSV KET QUA",
            command=self.export_csv,
            bg="#16a085",
            fg="white",
            pady=8
        ).pack(fill="x", padx=10, pady=10)

    def create_right_panel(self):
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Du lieu SV
        self.tab_data = tk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="Du lieu Sinh vien")

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

        # Tab 2: Thi truong lao dong
        self.tab_market = tk.Frame(self.notebook)
        self.notebook.add(self.tab_market, text="Thi truong Lao dong")

        self.txt_market = tk.Text(
            self.tab_market,
            font=("Consolas", 11),
            wrap="word"
        )
        self.txt_market.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 3: Bao cao san sang
        self.tab_report = tk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text="Bao cao San sang")

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
            spark = self.get_spark()
            self.spark_df = load_csv_file(spark, path)
            sample = self.spark_df.limit(2000).toPandas()
            self.show_table(sample)

            total = self.spark_df.count()
            messagebox.showinfo("Thanh cong", f"Da tai {total} sinh vien")
        except Exception as e:
            messagebox.showerror("Loi", str(e))

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
        if self.spark_df is None:
            messagebox.showwarning(
                "Chua co du lieu",
                "Vui long tai CSV diem sinh vien truoc."
            )
            return

        keyword = self.entry_search_sv.get().strip().lower()

        try:
            spark_df = self.spark_df.cache()

            result_df, real_jobs, important_subjects = CareerAnalyzer.analyze_students(
                spark_df,
                keyword,
                model_path=self.model_path.get()
            )

            if result_df is None or result_df.empty:
                messagebox.showinfo(
                    "Khong co du lieu",
                    "Khong tim thay sinh vien phu hop."
                )
                return

            self.df_career_result = result_df
            self.market_data = real_jobs
            self.important_subjects = important_subjects

            # Hien thi bang ket qua
            self.show_table(result_df)

            # Hien thi thi truong
            self.show_market_report(real_jobs, important_subjects)

            # Hien thi bao cao chi tiet
            self.show_readiness_report(result_df)

            messagebox.showinfo(
                "Hoan tat",
                f"Da phan tich {len(result_df)} sinh vien."
            )

        except Exception as e:
            messagebox.showerror("Loi Phan Tich", str(e))

    def show_market_report(self, real_jobs, important_subjects):
        """Hien thi tab Thi truong Lao dong (Macro Stats)"""
        self.txt_market.delete(1.0, tk.END)

        self.txt_market.insert(tk.END, "=" * 60 + "\n")
        self.txt_market.insert(tk.END, "  DU LIEU THI TRUONG IT THUC TE (TOPDEV MACRO API)\n")
        self.txt_market.insert(tk.END, "=" * 60 + "\n\n")
        
        if not real_jobs:
            self.txt_market.insert(tk.END, "  (Chua co du lieu thi truong. Vui long chay Crawl Market Data)\n\n")
        else:
            # Tinh tong so bai tuyen dung IT
            total_it = 0
            for job in real_jobs:
                if job.get("Category", "") == "IT":
                    try:
                        total_it += int(job.get("JobCount", 0))
                    except:
                        pass
            
            self.txt_market.insert(tk.END, f"  Tong so viec lam Nganh IT hien tai: {total_it} jobs\n\n")
            self.txt_market.insert(tk.END, "  [PHAN BO THEO CHUYEN NGANH (ROLES)]:\n")
            
            # Sort by job count
            sorted_jobs = []
            for job in real_jobs:
                if job.get("Category", "") == "IT":
                    try:
                        count = int(job.get("JobCount", 0))
                        sorted_jobs.append((job.get("Role", "N/A"), count))
                    except:
                        pass
            sorted_jobs.sort(key=lambda x: x[1], reverse=True)
            
            for role, count in sorted_jobs:
                ratio = (count / max(total_it, 1)) * 100
                bar = "|" * int(ratio / 2)
                self.txt_market.insert(tk.END, f"  + {role[:35]:<35}: {count:<4} Jobs ({ratio:4.1f}%) {bar}\n")
            self.txt_market.insert(tk.END, "\n")

        if important_subjects:
            self.txt_market.insert(tk.END, "-" * 60 + "\n")
            self.txt_market.insert(tk.END, "  TOP MON HOC ANH HUONG DEN SAN SANG NGHE NGHIEP\n")
            self.txt_market.insert(tk.END, "  (Decision Tree Feature Importance)\n")
            self.txt_market.insert(tk.END, "-" * 60 + "\n\n")

            from scripts.createdata import SUBJECT_NAMES
            for code, importance in important_subjects:
                name = SUBJECT_NAMES.get(code, code)
                bar = "#" * int(importance / 2)
                self.txt_market.insert(
                    tk.END,
                    f"    {code} ({name}): {importance}% {bar}\n"
                )

    def show_readiness_report(self, result_df):
        """Hien thi tab Bao cao San sang & Matching"""
        self.txt_report.delete(1.0, tk.END)
        self.notebook.select(self.tab_report)

        self.txt_report.insert(
            tk.END,
            f"DA PHAN TICH {len(result_df)} SINH VIEN\n\n"
        )

        # Thong ke tong quan
        if "nhom_san_sang" in result_df.columns:
            self.txt_report.insert(tk.END, "=" * 60 + "\n")
            self.txt_report.insert(tk.END, "  1. MUC DO SAN SANG (READINESS ML MODEL)\n")
            self.txt_report.insert(tk.END, "=" * 60 + "\n\n")

            counts = result_df["nhom_san_sang"].value_counts()
            total = len(result_df)
            for group, count in counts.items():
                pct = count / total * 100
                bar = "|" * int(pct / 2)
                self.txt_report.insert(
                    tk.END,
                    f"  {group[:20]:20s}: {count:4d} SV ({pct:5.1f}%) {bar}\n"
                )
            self.txt_report.insert(tk.END, "\n")

        # Chi tiet tung SV
        self.txt_report.insert(tk.END, "=" * 60 + "\n")
        self.txt_report.insert(tk.END, "  2. DANH GIA CO HOI & LO TRINH NGHE NGHIEP (MACRO MAPPING)\n")
        self.txt_report.insert(tk.END, "=" * 60 + "\n\n")

        for idx, row in result_df.iterrows():
            if idx >= 50:  # Gioi han hien thi 50 SV
                self.txt_report.insert(tk.END, f"\n... va {len(result_df) - 50} sinh vien khac.\n")
                break

            ma_sv = row.get("ma_sv", "")
            ho_ten = row.get("ho_ten", "")
            gpa = row.get("gpa_tong", 0)
            nhom = row.get("nhom_san_sang", "")
            toeic = row.get("TOEIC", 0)
            matched_track = row.get("top_matched_jobs", "Khong tim thay")

            self.txt_report.insert(tk.END, f"  SINH VIEN {idx + 1}: {ma_sv} - {ho_ten}\n")
            self.txt_report.insert(tk.END, f"    GPA tong        : {gpa}/4.0\n")
            self.txt_report.insert(tk.END, f"    TOEIC           : {toeic}\n")
            self.txt_report.insert(tk.END, f"    Muc do San sang : {nhom}\n")
            
            self.txt_report.insert(tk.END, f"\n    >> PHAN TICH THE MANH VÀ CO HOI THI TRUONG:\n")
            for line in matched_track.split("\n"):
                self.txt_report.insert(tk.END, f"       {line}\n")
            
            self.txt_report.insert(tk.END, "\n" + "-" * 60 + "\n\n")

    def export_csv(self):
        if self.df_career_result is None:
            messagebox.showwarning("Chua co du lieu", "Chua co ket qua.")
            return

        import os
        default_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "output")
        os.makedirs(default_dir, exist_ok=True)

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialdir=default_dir,
            initialfile="danh_gia_san_sang_nghe_nghiep.csv"
        )

        if path:
            try:
                self.df_career_result.to_csv(path, index=False, encoding="utf-8-sig")
                messagebox.showinfo("Hoan tat", "Da xuat file CSV.")
            except Exception as e:
                messagebox.showerror("Loi", str(e))
