import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pyspark.sql import SparkSession
from src.utils.data_utils import load_csv_file
from src.services.student_predictor import StudentPredictorService


# ══════════════════════════════════════════════════════════════════════════════
# Cluster metadata  –  GPA theo THANG 4
# Cluster ID từ StudentPredictorService:
#   2 → Nguy hiểm (risk_order 0)
#   0 → Trung bình (risk_order 1)
#   3 → Khá        (risk_order 2)
#   1 → Xuất sắc   (risk_order 3)
# ══════════════════════════════════════════════════════════════════════════════
CLUSTER_INFO = {
    2: {
        "label":     "Yếu – Nguy Cơ Cao",
        "risk":      "🚨  Rủi ro cao",
        "color_tag": "danger",
        "badge_bg":  "#ef4444",
        "badge_fg":  "#ffffff",
        "icon":      "⚡",
        "gpa_range": "< 2.0",
        "description": (
            "Sinh viên thuộc nhóm có kết quả học tập đáng lo ngại. "
            "GPA thấp, nhiều môn chưa đạt, nguy cơ bị cảnh báo "
            "học tập hoặc buộc thôi học nếu không can thiệp kịp thời."
        ),
        "reasons": [
            "GPA dưới 2.0 – dưới mức yêu cầu tối thiểu",
            "Số môn trượt (điểm gốc < 4.0/10) ở mức cao",
            "Điểm số biến động lớn, thiếu ổn định",
            "Không có hoặc rất ít môn học xuất sắc",
        ],
        "suggestions": [
            "Gặp ngay cố vấn học tập để được hỗ trợ kịp thời",
            "Đăng ký học lại các môn chưa đạt trong kỳ tới",
            "Xây dựng lại phương pháp học tập phù hợp",
            "Cân nhắc hỗ trợ tâm lý nếu có khó khăn ngoài học tập",
        ],
    },
    0: {
        "label":     "Trung Bình – Cần Cố Gắng",
        "risk":      "⚠️  Rủi ro trung bình",
        "color_tag": "warning",
        "badge_bg":  "#f59e0b",
        "badge_fg":  "#1c1917",
        "icon":      "📘",
        "gpa_range": "2.0 – 2.5",
        "description": (
            "Sinh viên đạt mức trung bình, vượt ngưỡng an toàn nhưng chưa "
            "nổi bật. Điểm còn phân tán, một số môn cần cải thiện thêm "
            "để tránh rủi ro học vụ."
        ),
        "reasons": [
            "GPA trong khoảng 2.0 – 2.5",
            "Còn một số môn trượt hoặc điểm thấp cần khắc phục",
            "Điểm số chưa đồng đều giữa các học phần",
            "Chưa có nhiều môn xuất sắc để nâng cao GPA",
        ],
        "suggestions": [
            "Xây dựng lịch học đều đặn, ưu tiên môn yếu",
            "Tham gia nhóm học tập, trao đổi bài cùng bạn",
            "Gặp giảng viên để được hướng dẫn thêm ở môn khó",
        ],
    },
    3: {
        "label":     "Khá – Tiến Bộ Tốt",
        "risk":      "🔵  Rủi ro thấp",
        "color_tag": "good",
        "badge_bg":  "#3b82f6",
        "badge_fg":  "#ffffff",
        "icon":      "📈",
        "gpa_range": "2.5 – 3.2",
        "description": (
            "Sinh viên có kết quả khá, nắm chắc kiến thức cốt lõi và "
            "thể hiện sự tiến bộ ổn định. Với thêm nỗ lực, hoàn toàn "
            "có thể tiến lên nhóm xuất sắc."
        ),
        "reasons": [
            "GPA trong khoảng 2.5 – 3.2",
            "Rất ít hoặc không có môn trượt",
            "Phần lớn học phần đạt từ khá trở lên",
            "Điểm tương đối ổn định qua các học kỳ",
        ],
        "suggestions": [
            "Tập trung nâng điểm các môn còn ở mức trung bình",
            "Đặt mục tiêu GPA tăng thêm 0.2 – 0.3 mỗi kỳ",
            "Tham gia các hoạt động học thuật, seminar",
        ],
    },
    1: {
        "label":     "Xuất Sắc – Tiếp Tục Phát Huy",
        "risk":      "✅  Rủi ro thấp",
        "color_tag": "excellent",
        "badge_bg":  "#10b981",
        "badge_fg":  "#ffffff",
        "icon":      "🏆",
        "gpa_range": "3.2 – 4.0",
        "description": (
            "Sinh viên có thành tích xuất sắc, GPA cao và đồng đều trên "
            "hầu hết học phần. Đây là nhóm tiềm năng nhất, sẵn sàng cho "
            "học bổng và nghiên cứu khoa học."
        ),
        "reasons": [
            "GPA từ 3.2 trở lên",
            "Không có môn trượt, điểm đồng đều và ổn định",
            "Nhiều môn đạt điểm xuất sắc (≥ 8.0/10)",
            "Kết quả học tập vượt trội so với toàn khóa",
        ],
        "suggestions": [
            "Đăng ký tham gia nghiên cứu khoa học, đề tài bộ môn",
            "Ứng tuyển học bổng trong và ngoài nước",
            "Hỗ trợ và hướng dẫn các bạn trong nhóm học tập",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Helpers  –  tất cả dựa trên
# ══════════════════════════════════════════════════════════════════════════════

def gpa4_color(gpa4: float) -> str:
    """Màu theo GPA (0–4)."""
    if gpa4 >= 3.2:
        return "#10b981"   # xanh lá  – Giỏi / Xuất sắc
    if gpa4 >= 2.5:
        return "#3b82f6"   # xanh dương – Khá
    if gpa4 >= 2.0:
        return "#f59e0b"   # vàng – Trung bình
    return "#ef4444"       # đỏ – Yếu


def gpa4_label(gpa4: float) -> str:
    """Xếp loại học lực theo GPA."""
    if gpa4 >= 3.6:
        return "Xuất sắc"
    if gpa4 >= 3.2:
        return "Giỏi"
    if gpa4 >= 2.5:
        return "Khá"
    if gpa4 >= 2.0:
        return "Trung bình"
    return "Yếu"


def stddev_color(std: float) -> str:
    """Nhỏ = ổn định = xanh; lớn = dao động = đỏ."""
    if std <= 0.3:
        return "#10b981"
    if std <= 0.6:
        return "#3b82f6"
    if std <= 0.9:
        return "#f59e0b"
    return "#ef4444"


def stddev_label(std: float) -> str:
    if std <= 0.3:
        return "Rất ổn định"
    if std <= 0.6:
        return "Ổn định"
    if std <= 0.9:
        return "Dao động"
    return "Không ổn định"


def failed_color(n: int) -> str:
    """ÍT môn trượt = TỐT = xanh; NHIỀU môn trượt = XẤU = đỏ."""
    if n == 0:
        return "#10b981"
    if n <= 2:
        return "#3b82f6"
    if n <= 5:
        return "#f59e0b"
    return "#ef4444"


def failed_label(n: int) -> str:
    if n == 0:
        return "Không có môn trượt ✓"
    if n <= 2:
        return f"{n} môn – Ít, cần khắc phục"
    if n <= 5:
        return f"{n} môn – Trung bình, cần chú ý"
    return f"{n} môn – Nhiều, rủi ro cao"


def excellent_color(n: int, total: int) -> str:
    """NHIỀU môn xuất sắc = tốt = xanh."""
    ratio = n / total if total else 0
    if ratio >= 0.5:
        return "#10b981"
    if ratio >= 0.3:
        return "#3b82f6"
    if ratio >= 0.1:
        return "#f59e0b"
    return "#6b7280"


# ══════════════════════════════════════════════════════════════════════════════
# Popup chi tiết sinh viên
# ══════════════════════════════════════════════════════════════════════════════
class StudentDetailPopup(tk.Toplevel):
    """Hiển thị khi click vào sinh viên trong bảng."""

    POPUP_W = 620
    POPUP_H = 600

    # Tổng số môn trong bộ dữ liệu (data_demo.csv có 37 môn)
    TOTAL_SUBJECTS = 37

    def __init__(self, parent, row_data: dict):
        super().__init__(parent)
        self.title("Chi Tiết Sinh Viên")
        self.resizable(False, False)
        self.configure(bg="#0f172a")
        self.grab_set()  # modal – focus vào popup

        # Căn giữa màn hình
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - self.POPUP_W) // 2
        y = (self.winfo_screenheight() - self.POPUP_H) // 2
        self.geometry(f"{self.POPUP_W}x{self.POPUP_H}+{x}+{y}")

        # ── Đọc dữ liệu từ row ──────────────────────────────────────────────
        cluster = int(row_data.get("prediction", 1))
        info    = CLUSTER_INFO.get(cluster, CLUSTER_INFO[1])
        ma_sv   = str(row_data.get("ma_sv",  "–"))
        ho_ten  = str(row_data.get("ho_ten", "–"))

        try:
            gpa    = float(row_data.get("gpa", 0))
        except (ValueError, TypeError):
            gpa    = 0.0
        try:
            std    = float(row_data.get("std_score", 0))
        except (ValueError, TypeError):
            std    = 0.0
        try:
            failed = int(float(row_data.get("failed_subjects", 0)))
        except (ValueError, TypeError):
            failed = 0
        try:
            excel  = int(float(row_data.get("excellent_subjects", 0)))
        except (ValueError, TypeError):
            excel  = 0

        self._build_header(ma_sv, ho_ten, gpa, info)
        self._build_body(info, gpa, std, failed, excel)
        self._build_footer()

    # ── Header ───────────────────────────────────────────────────────────────
    def _build_header(self, ma_sv, ho_ten, gpa, info):
        hdr = tk.Frame(self, bg=info["badge_bg"], padx=20, pady=14)
        hdr.pack(fill="x")

        # Trái: icon + tên SV
        left = tk.Frame(hdr, bg=info["badge_bg"])
        left.pack(side="left")

        tk.Label(left, text=info["icon"],
                 font=("Segoe UI Emoji", 28),
                 bg=info["badge_bg"], fg=info["badge_fg"]
                 ).pack(side="left", padx=(0, 12))

        name_f = tk.Frame(left, bg=info["badge_bg"])
        name_f.pack(side="left")
        tk.Label(name_f, text=ho_ten,
                 font=("Segoe UI", 14, "bold"),
                 bg=info["badge_bg"], fg=info["badge_fg"]
                 ).pack(anchor="w")
        tk.Label(name_f, text=f"Mã SV: {ma_sv}",
                 font=("Segoe UI", 9),
                 bg=info["badge_bg"], fg=info["badge_fg"]
                 ).pack(anchor="w")

        # Phải: GPA card + nhóm
        right = tk.Frame(hdr, bg=info["badge_bg"])
        right.pack(side="right")

        # Card GPA – dùng thang 4
        gpa_card = tk.Frame(right, bg="#ffffff", padx=14, pady=8)
        gpa_card.pack(side="right", padx=(10, 0))
        tk.Label(gpa_card, text="GPA",
                 font=("Segoe UI", 8, "bold"),
                 bg="#ffffff", fg="#6b7280").pack()
        tk.Label(gpa_card, text=f"{gpa:.2f}",
                 font=("Segoe UI", 20, "bold"),
                 bg="#ffffff", fg=gpa4_color(gpa)).pack()
        tk.Label(gpa_card, text=gpa4_label(gpa),
                 font=("Segoe UI", 8),
                 bg="#ffffff", fg=gpa4_color(gpa)).pack()

        # Nhóm + rủi ro
        badge = tk.Frame(right, bg=info["badge_bg"])
        badge.pack(side="right")
        tk.Label(badge, text=info["label"],
                 font=("Segoe UI", 9, "bold"),
                 bg=info["badge_bg"], fg=info["badge_fg"]
                 ).pack(anchor="e")
        tk.Label(badge, text=info["risk"],
                 font=("Segoe UI", 9),
                 bg=info["badge_bg"], fg=info["badge_fg"]
                 ).pack(anchor="e")

    # ── Body ─────────────────────────────────────────────────────────────────
    def _build_body(self, info, gpa, std, failed, excel):
        outer = tk.Frame(self, bg="#f1f5f9")
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg="#f1f5f9", highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg="#f1f5f9")
        win  = canvas.create_window((0, 0), window=body, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=canvas.winfo_width())

        body.bind("<Configure>", _resize)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

        P = {"padx": 16, "pady": (0, 8)}
        total = self.TOTAL_SUBJECTS

        # ── 1. Chỉ số học tập (4 thẻ) ────────────────────────────────────────
        self._sec_title(body, "📊  Chỉ Số Học Tập")

        cards = tk.Frame(body, bg="#f1f5f9")
        cards.pack(fill="x", **P)

        # GPA thang 4: 4.0 là tuyệt đối → bar_pct = gpa/4
        self._metric_card(
            cards,
            title="GPA",
            value=f"{gpa:.2f}",
            subtitle=gpa4_label(gpa),
            color=gpa4_color(gpa),
            bar_pct=gpa / 4.0,           # 4.0 = 100%
        )

        # Độ lệch chuẩn: nhỏ = tốt → bar đảo (thấp = đầy)
        self._metric_card(
            cards,
            title="Độ lệch chuẩn",
            value=f"{std:.2f}",
            subtitle=stddev_label(std),
            color=stddev_color(std),
            bar_pct=max(0.0, 1.0 - std / 1.5),   # đảo ngược: nhỏ=bar đầy
        )

        # Môn trượt: ít = tốt → bar đảo (0 môn = bar đầy)
        self._metric_card(
            cards,
            title="Môn trượt",
            value=str(failed),
            subtitle=failed_label(failed),
            color=failed_color(failed),
            bar_pct=max(0.0, 1.0 - failed / max(total, 1)),  # đảo ngược
        )

        # Môn xuất sắc: nhiều = tốt → bar thuận (nhiều = bar đầy)
        excel_pct = round(excel / total * 100) if total else 0
        self._metric_card(
            cards,
            title="Môn xuất sắc",
            value=str(excel),
            subtitle=f"{excel_pct}% tổng số môn",
            color=excellent_color(excel, total),
            bar_pct=excel / max(total, 1),
        )

        # ── 2. Mô tả nhóm ────────────────────────────────────────────────────
        self._sec_title(body, "📋  Mô Tả Nhóm Phân Loại")
        desc_f = tk.Frame(body, bg="#e2e8f0", padx=14, pady=12)
        desc_f.pack(fill="x", padx=20, pady=(0, 8)) 
        tk.Label(desc_f, text=info["description"],
                 font=("Segoe UI", 10), bg="#e2e8f0", fg="#1e293b",
                 wraplength=520, justify="left").pack(anchor="w", padx =4)

        # ── 3. Lý do xếp nhóm ────────────────────────────────────────────────
        self._sec_title(body, "🔍  Lý Do Xếp Vào Nhóm Này")
        reasons_f = tk.Frame(body, bg="#e2e8f0", padx=14, pady=10)
        reasons_f.pack(fill="x", **P)
        for r in info["reasons"]:
            row = tk.Frame(reasons_f, bg="#e2e8f0")
            row.pack(fill="x", pady=2)
            tk.Label(row, text="▸", font=("Segoe UI", 11, "bold"),
                     bg="#e2e8f0", fg=info["badge_bg"]
                     ).pack(side="left", padx=(0, 6))
            tk.Label(row, text=r, font=("Segoe UI", 10),
                     bg="#e2e8f0", fg="#1e293b", anchor="w"
                     ).pack(side="left", fill="x", expand=True)

        # ── 4. Gợi ý cải thiện ───────────────────────────────────────────────
        self._sec_title(body, "💡  Gợi Ý Cải Thiện")
        sug_f = tk.Frame(body, bg="#e2e8f0", padx=14, pady=10)
        sug_f.pack(fill="x", padx=16, pady=(0, 16))
        for s in info["suggestions"]:
            row = tk.Frame(sug_f, bg="#e2e8f0")
            row.pack(fill="x", pady=2)
            tk.Label(row, text="→", font=("Segoe UI", 10, "bold"),
                     bg="#e2e8f0", fg="#f59e0b"
                     ).pack(side="left", padx=(0, 6))
            tk.Label(row, text=s, font=("Segoe UI", 10),
                     bg="#e2e8f0", fg="#000000", anchor="w"
                     ).pack(side="left", fill="x", expand=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        ft = tk.Frame(self, bg="#f1f5f9", pady=8)
        ft.pack(fill="x", side="bottom")
        tk.Button(ft, text="✕  Đóng", command=self.destroy,
                  bg="#ef3030", fg="#f8f8f8",
                  font=("Segoe UI", 10), relief="flat",
                  padx=24, pady=6, cursor="hand2",
                  activebackground="#334155", activeforeground="#e2e8f0"
                  ).pack()

    # ── Tiêu đề section ──────────────────────────────────────────────────────
    def _sec_title(self, parent, text):
        tk.Label(parent, text=text,
                 font=("Segoe UI", 10, "bold"),
                 bg="#f1f5f9", fg="#94a3b8", anchor="w"
                 ).pack(fill="x", padx=16, pady=(12, 4))

    # ── Thẻ chỉ số ───────────────────────────────────────────────────────────
    def _metric_card(self, parent, title, value, subtitle,
                     color, bar_pct: float):
        """
        Một thẻ chỉ số kèm progress bar.
        bar_pct: 0.0–1.0, luôn cao = tốt (đã xử lý đảo ngược ở caller).
        """
        card = tk.Frame(parent, bg="#e2e8f0", padx=10, pady=10)
        card.pack(side="left", expand=True, fill="x", padx=4)

        tk.Label(card, text=title,
                 font=("Segoe UI", 8, "bold"),
                 bg="#e2e8f0", fg="#64748b").pack(anchor="w")

        tk.Label(card, text=value,
                 font=("Segoe UI", 20, "bold"),
                 bg="#e2e8f0", fg=color).pack(anchor="w")

        tk.Label(card, text=subtitle,
                 font=("Segoe UI", 8),
                 bg="#e2e8f0", fg=color).pack(anchor="w")

        # Progress bar – màu phản ánh mức độ tốt/xấu
        bar_bg = tk.Frame(card, bg="#374151", height=5)
        bar_bg.pack(fill="x", pady=(6, 2))
        bar_bg.pack_propagate(False)
        bar_pct = max(0.0, min(1.0, bar_pct))
        if bar_pct > 0:
            tk.Frame(bar_bg, bg=color, height=5).place(
                relx=0, rely=0, relwidth=bar_pct, relheight=1
            )


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

    # cluster_id → row color tag
    CLUSTER_TAG = {2: "danger", 0: "warning", 3: "good", 1: "excellent"}

    def __init__(self, parent):
        self.parent        = parent
        self.spark         = None
        self._row_data_map = {}
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
        # Toolbar
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

        self.status_label = tk.Label(
            toolbar, text="Chưa tải dữ liệu",
            font=("Segoe UI", 9), bg="#e2e8f0", fg="#000000"
        )
        self.status_label.pack(side="left", padx=16)

        # Legend
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

        # Treeview + scrollbars
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
            result    = StudentPredictorService.predict_students(spark_df, spark)
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

        # Hiển thị đúng các cột service trả về, không tính lại
        display_cols = [c for c in self.OUTPUT_COLS if c in df.columns]

        self.tree["columns"] = display_cols
        self.tree["show"]    = "headings"

        for col in display_cols:
            self.tree.heading(col, text=self.COL_HEADERS.get(col, col))
            self.tree.column(col,
                             width=self.COL_WIDTHS.get(col, 100),
                             anchor="center", minwidth=60)

        # Row color theo cluster
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