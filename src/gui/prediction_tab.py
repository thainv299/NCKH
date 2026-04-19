import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pyspark.sql import SparkSession
from src.utils.data_utils import load_csv_file
from src.services.student_predictor import StudentPredictorService
from src.gui.student_detail_pop_up import CLUSTER_INFO, StudentDetailPopup


# ══════════════════════════════════════════════════════════════════════════════
# Tab chính
# ══════════════════════════════════════════════════════════════════════════════
class StudentPredictionTab:
    """
    Hiển thị bảng kết quả đúng như output của StudentPredictorService:
      ma_sv | ho_ten | gpa | std_score | failed_subjects
      | excellent_subjects | prediction
    Không tự tính lại bất cứ cột nào.
    """

    OUTPUT_COLS = [
        "ma_sv", "ho_ten", "gpa", "std_score",
        "failed_subjects", "excellent_subjects", "prediction",
    ]

    COL_HEADERS = {
        "ma_sv":              "Mã SV",
        "ho_ten":             "Họ Tên",
        "gpa":                "GPA",
        "std_score":          "Độ lệch chuẩn",
        "failed_subjects":    "Môn trượt",
        "excellent_subjects": "Môn xuất sắc",
        "prediction":         "Nhóm",
    }

    COL_WIDTHS = {
        "ma_sv":              90,
        "ho_ten":             140,
        "gpa":                110,
        "std_score":          120,
        "failed_subjects":    90,
        "excellent_subjects": 100,
        "prediction":         70,
    }

    CLUSTER_TAG = {2: "danger", 0: "warning", 3: "good", 1: "excellent"}

    def __init__(self, parent):
        self.parent        = parent
        self.spark         = None
        self._row_data_map = {}
        self.model_path    = tk.StringVar(value="models/student_analysis_kmeans_model")
        self.create_layout()

    def get_spark(self):
        if self.spark is None:
            self.spark = (
                SparkSession.builder
                .appName("Student Prediction")
                .master("local[*]")
                .getOrCreate()
            )
        return self.spark

    # ── Layout ─────────────────────────────────────────────────────────────
    def create_layout(self):
        toolbar = tk.Frame(self.parent, bg="#e2e8f0", pady=10, padx=12)
        toolbar.pack(fill="x")

        tk.Button(
            toolbar, text="📂  Tải CSV & Dự Đoán",
            command=self.load_and_predict,
            bg="#3b82f6", fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=6, cursor="hand2",
            activebackground="#2563eb", activeforeground="white",
        ).pack(side="left")

        # Thêm phần chọn model
        model_frame = tk.Frame(toolbar, bg="#e2e8f0")
        model_frame.pack(side="left", padx=20)
        
        tk.Label(model_frame, text="Model:", bg="#e2e8f0", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Entry(model_frame, textvariable=self.model_path, width=30, font=("Segoe UI", 9)).pack(side="left", padx=5)
        tk.Button(model_frame, text="...", command=self.browse_model, width=3).pack(side="left")

        self.status_label = tk.Label(
            toolbar, text="Chưa tải dữ liệu",
            font=("Segoe UI", 9), bg="#e2e8f0", fg="#000000"
        )
        self.status_label.pack(side="left", padx=16)

        legend = tk.Frame(self.parent, bg="#f1f5f9", pady=6, padx=12)
        legend.pack(fill="x")
        tk.Label(legend, text="Phân loại nhóm:  ",
                 font=("Segoe UI", 15, "bold"),
                 bg="#f1f5f9", fg="#040404").pack(side="left")
        for cid, cinfo in CLUSTER_INFO.items():
            f = tk.Frame(legend, bg="#e2e8f0")
            f.pack(side="left", padx=6)
            tk.Label(f, text="●", font=("Segoe UI", 12),
                     bg="#f1f5f9", fg=cinfo["badge_bg"]).pack(side="left")
            tk.Label(f, text=cinfo["label"], font=("Segoe UI", 10),
                     bg="#f1f5f9", fg="#000000").pack(side="left")

        tk.Label(
            self.parent,
            text="💡 Click vào dòng bất kỳ để xem chi tiết và lý do xếp nhóm",
            font=("Segoe UI", 8, "italic"),
            bg="#f1f5f9", fg="#475569"
        ).pack(anchor="w", padx=12, pady=(2, 4))

        tree_frame = tk.Frame(self.parent, bg="#f1f5f9")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                         background="#f1f5f9", foreground="#e2e8f0",
                         fieldbackground="#f1f5f9", rowheight=26,
                         font=("Segoe UI", 9))
        style.configure("Custom.Treeview.Heading",
                         background="#f1f5f9", foreground="#000000",
                         font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Custom.Treeview",
                  background=[("selected", "#334155")],
                  foreground=[("selected", "#f8fafc")])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        self.tree = ttk.Treeview(
            tree_frame, style="Custom.Treeview",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
            selectmode="browse"
        )
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<ButtonRelease-1>", self.on_row_click)
        self.tree.bind("<Return>",           self.on_row_click)

    def browse_model(self):
        dirname = filedialog.askdirectory(title="Chọn thư mục model",
                                        initialdir="models")
        if dirname:
            # Chuyển sang đường dẫn tương đối nếu có thể
            try:
                rel_path = os.path.relpath(dirname, os.getcwd())
                self.model_path.set(rel_path)
            except ValueError:
                self.model_path.set(dirname)

    # ── Load & Predict ─────────────────────────────────────────────────────
    def load_and_predict(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return

        self.status_label.config(text="⏳  Đang xử lý...", fg="#f59e0b")
        self.parent.update_idletasks()

        try:
            spark     = self.get_spark()
            spark_df  = load_csv_file(spark, path)
            model_p   = self.model_path.get()
            result    = StudentPredictorService.predict_students(spark_df, spark, model_path=model_p)
            result_pd = result.limit(2000).toPandas()
            self.show_table(result_pd)
            self.status_label.config(
                text=(f"✅  Đã tải {len(result_pd)} sinh viên"
                      " – nhấn vào dòng để xem chi tiết"),
                fg="#10b981"
            )
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            self.status_label.config(text="❌  Lỗi khi tải dữ liệu", fg="#ef4444")

    # ── Show Table ─────────────────────────────────────────────────────────
    def show_table(self, df):
        self.tree.delete(*self.tree.get_children())
        self._row_data_map.clear()

        display_cols = [c for c in self.OUTPUT_COLS if c in df.columns]

        self.tree["columns"] = display_cols
        self.tree["show"]    = "headings"

        for col in display_cols:
            self.tree.heading(col, text=self.COL_HEADERS.get(col, col))
            self.tree.column(col,
                             width=self.COL_WIDTHS.get(col, 100),
                             anchor="center", minwidth=60)

        self.tree.tag_configure("danger",    background="#fd7e7e", foreground="#000000")
        self.tree.tag_configure("warning",   background="#fcd143", foreground="#000000")
        self.tree.tag_configure("good",      background="#7cb8fc", foreground="#000000")
        self.tree.tag_configure("excellent", background="#5eecb3", foreground="#000000")

        for _, row in df.iterrows():
            try:
                cluster = int(row.get("prediction", 1))
            except (ValueError, TypeError):
                cluster = 1

            tag    = self.CLUSTER_TAG.get(cluster, "good")
            values = [row[c] for c in display_cols]
            iid    = self.tree.insert("", "end", values=values, tags=(tag,))
            self._row_data_map[iid] = row.to_dict()

    # ── Click → Popup ──────────────────────────────────────────────────────
    def on_row_click(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        row_data = self._row_data_map.get(selected[0])
        if row_data:
            StudentDetailPopup(self.parent, row_data)