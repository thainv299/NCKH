"""
Giao diện Tab phân tích xu hướng nghề nghiệp
"""
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from utils.data_utils import load_csv_file
from services.career_analyzer import CareerAnalyzer

class CareerAnalysisTab:
    """
    Class quản lý giao diện và logic Tab xu hướng nghề nghiệp
    """
    
    def __init__(self, parent_frame):
        self.parent = parent_frame
        
        # Dữ liệu
        self.df_student = None
        self.df_career_result = None
        
        # Tạo giao diện
        self.create_layout()
    
    def create_layout(self):
        """Tạo bố cục chính"""
        self.paned = tk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)
        
        self.left_frame = tk.Frame(self.paned, bg="#f7f7f7", width=280)
        self.right_frame = tk.Frame(self.paned, bg="white")
        
        self.paned.add(self.left_frame, minsize=250, width=280)
        self.paned.add(self.right_frame)
        
        self.create_left_panel()
        self.create_right_panel()
    
    def create_left_panel(self):
        """Tạo panel điều khiển bên trái"""
        # Container cho nội dung có thể scroll
        content_frame = tk.Frame(self.left_frame, bg="#f7f7f7")
        content_frame.pack(fill="both", expand=True)
        
        # Canvas và Scrollbar
        canvas = tk.Canvas(content_frame, bg="#f7f7f7", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f7f7f7")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Cho phép scroll bằng chuột
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
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
            text="🔍 Tìm kiếm (Mã SV / Họ tên / Mã môn):",
            bg="#f7f7f7"
        ).pack(anchor="w", padx=10)
        
        self.entry_search_sv = tk.Entry(scrollable_frame)
        self.entry_search_sv.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            scrollable_frame,
            text="📝 TẠO BÁO CÁO XU HƯỚNG",
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
        """Tạo panel hiển thị bên phải"""
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # TAB 1: Dữ liệu sinh viên
        self.tab_data = tk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="📋 Dữ liệu Sinh viên")
        
        search_frame = tk.Frame(self.tab_data, bg="#ecf0f1")
        search_frame.pack(fill="x")
        
        tk.Label(
            search_frame, 
            text="🔍 Tìm kiếm:", 
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=10)
        
        self.entry_filter_sv = tk.Entry(search_frame, width=40)
        self.entry_filter_sv.pack(side=tk.LEFT, padx=5)
        self.entry_filter_sv.bind("<KeyRelease>", self.filter_table)
        
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
        
        # TAB 2: Báo cáo
        self.tab_report = tk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text="📄 Báo cáo Xu hướng")
        
        report_frame = tk.Frame(self.tab_report)
        report_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scroll = ttk.Scrollbar(report_frame)
        self.txt_report = tk.Text(
            report_frame,
            font=("Consolas", 11),
            yscrollcommand=scroll.set,
            wrap="word"
        )
        scroll.config(command=self.txt_report.yview)
        
        scroll.pack(side=tk.RIGHT, fill="y")
        self.txt_report.pack(side=tk.LEFT, fill="both", expand=True)
        
        # Định dạng text tags
        self.txt_report.tag_configure(
            "header", 
            font=("Arial", 13, "bold"), 
            foreground="#2980b9"
        )
        self.txt_report.tag_configure(
            "sub", 
            font=("Arial", 11, "bold")
        )
        self.txt_report.tag_configure("content", font=("Consolas", 11))
        self.txt_report.tag_configure("divider", foreground="#bdc3c7")
    
    # ================= LOGIC XỬ LÝ =================
    
    def load_student_csv(self):
        """Tải file CSV điểm sinh viên"""
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        
        try:
            df = load_csv_file(path)
            self.df_student = df.copy()
            self.show_table(df)
            messagebox.showinfo(
                "Thành công",
                f"Đã tải CSV sinh viên ({len(df)} dòng)"
            )
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
    
    def show_table(self, df):
        """Hiển thị dữ liệu lên Treeview"""
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
    
    def filter_table(self, event=None):
        """Lọc dữ liệu trong bảng"""
        if self.df_student is None:
            return
        
        keyword = self.entry_filter_sv.get().strip().lower()
        df = self.df_student
        
        if not keyword:
            self.show_table(df)
            return
        
        mask = df.astype(str).apply(
            lambda col: col.str.lower().str.contains(keyword, na=False, regex=False)
        ).any(axis=1)
        
        self.show_table(df[mask])
    
    def analyze_career(self):
        """Phân tích xu hướng nghề nghiệp"""
        if self.df_student is None:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Vui lòng tải CSV điểm sinh viên trước."
            )
            return
        
        keyword = self.entry_search_sv.get().strip().lower()
        
        try:
            # Phân tích
            result_df, report_lines = CareerAnalyzer.analyze_students(
                self.df_student, 
                keyword
            )
            
            if result_df is None or result_df.empty:
                messagebox.showinfo(
                    "Không có dữ liệu",
                    "Không tìm thấy sinh viên phù hợp."
                )
                return
            
            # Lưu kết quả
            self.df_career_result = result_df
            
            # Hiển thị báo cáo
            self.txt_report.delete(1.0, tk.END)
            self.notebook.select(self.tab_report)
            
            for line in report_lines:
                self.txt_report.insert(tk.END, line["text"], line["tag"])
            
            # Hiển thị bảng kết quả
            self.show_table(result_df)
            
            messagebox.showinfo(
                "Hoàn tất",
                f"Đã phân tích {len(result_df)} sinh viên."
            )
            
        except Exception as e:
            messagebox.showerror("Lỗi Phân Tích", str(e))
    
    def export_csv(self):
        """Xuất kết quả ra file CSV"""
        if not hasattr(self, "df_career_result") or self.df_career_result is None:
            messagebox.showwarning(
                "Chưa có dữ liệu", 
                "Chưa có kết quả để xuất."
            )
            return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="xu_huong_nghe_nghiep_sinh_vien.csv"
        )
        
        if path:
            try:
                self.df_career_result.to_csv(
                    path, 
                    index=False, 
                    encoding="utf-8-sig"
                )
                messagebox.showinfo("Hoàn tất", "Đã xuất file CSV.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")