"""
Giao diện Tab phân tích học phần
"""
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from utils.data_utils import load_csv_file
from services.subject_analyzer import SubjectAnalyzer

class SubjectAnalysisTab:
    """
    Class quản lý giao diện và logic Tab phân tích học phần
    """
    
    def __init__(self, parent_frame):
        self.parent = parent_frame
        
        # Dữ liệu
        self.df_pandas_original = None
        self.df_pandas_current = None
        self.selected_subjects_codes = []
        
        # Tạo giao diện
        self.create_layout()
    
    def create_layout(self):
        """Tạo bố cục chính"""
        self.paned_window = tk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)
        
        self.left_frame = tk.Frame(self.paned_window, bg="#f0f0f0", width=280)
        self.right_frame = tk.Frame(self.paned_window, bg="white")
        
        self.paned_window.add(self.left_frame, minsize=250, width=280)
        self.paned_window.add(self.right_frame)
        
        self.create_left_panel()
        self.create_right_panel()
    
    def create_left_panel(self):
        """Tạo panel điều khiển bên trái"""
        # Container cho nội dung có thể scroll
        content_frame = tk.Frame(self.left_frame, bg="#f0f0f0")
        content_frame.pack(fill="both", expand=True)
        
        # Canvas và Scrollbar
        canvas = tk.Canvas(content_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")
        
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
        
        # Header
        tk.Label(
            scrollable_frame, 
            text="ĐIỀU KHIỂN", 
            bg="#2c3e50", fg="white", 
            font=("Arial", 12, "bold"), pady=10
        ).pack(fill="x")
        
        # 1. Load File
        frame_file = tk.LabelFrame(
            scrollable_frame, 
            text="1. Dữ liệu nguồn", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0",
            padx=3,
            pady=3
        )
        frame_file.pack(fill="x", padx=5, pady=(5, 3))
        
        tk.Button(
            frame_file, 
            text="📂 Tải CSV", 
            command=self.load_csv, 
            bg="#3498db", 
            fg="white"
        ).pack(fill="x", padx=5, pady=3)
        
        self.lbl_file_status = tk.Label(
            frame_file, 
            text="Chưa có dữ liệu", 
            fg="gray", 
            bg="#f0f0f0"
        )
        self.lbl_file_status.pack(pady=2)
        
        # 2. Tìm kiếm & Thêm học phần
        frame_search = tk.LabelFrame(
            scrollable_frame, 
            text="2. Chọn học phần", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0",
            padx=3,
            pady=3
        )
        frame_search.pack(fill="x", padx=5, pady=3)
        
        tk.Label(
            frame_search, 
            text="Tìm kiếm (Tên/Mã):", 
            bg="#f0f0f0"
        ).pack(anchor="w", padx=5, pady=(3, 0))
        
        self.entry_search = tk.Entry(frame_search)
        self.entry_search.pack(fill="x", padx=5, pady=2)
        self.entry_search.bind("<Return>", lambda e: self.search_subject())
        
        tk.Button(
            frame_search, 
            text="🔍 Tìm", 
            command=self.search_subject, 
            bg="#95a5a6", 
            fg="white"
        ).pack(pady=3)
        
        self.combo_suggestions = ttk.Combobox(frame_search, state="readonly")
        self.combo_suggestions.pack(fill="x", padx=5, pady=3)
        
        tk.Button(
            frame_search, 
            text="⬇ Thêm vào danh sách phân tích", 
            command=self.add_subject_to_list,
            bg="#27ae60", 
            fg="white", 
            font=("Arial", 9, "bold")
        ).pack(fill="x", padx=5, pady=3)
        
        tk.Label(
            frame_search, 
            text="Danh sách các môn sẽ phân tích:", 
            bg="#f0f0f0", 
            font=("Arial", 9, "italic")
        ).pack(anchor="w", padx=5, pady=(3, 0))
        
        list_frame = tk.Frame(frame_search)
        list_frame.pack(fill="x", padx=5, pady=2)
        
        self.listbox_selected = tk.Listbox(list_frame, height=6)
        scrollbar_list = tk.Scrollbar(
            list_frame, 
            orient="vertical", 
            command=self.listbox_selected.yview
        )
        self.listbox_selected.config(yscrollcommand=scrollbar_list.set)
        
        self.listbox_selected.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar_list.pack(side=tk.RIGHT, fill="y")
        
        tk.Button(
            frame_search, 
            text="❌ Xóa danh sách chọn", 
            command=self.clear_selection, 
            bg="#e74c3c", 
            fg="white"
        ).pack(pady=3)
        
        # 3. Tùy chọn Phân tích
        frame_opt = tk.LabelFrame(
            scrollable_frame, 
            text="3. Cấu hình báo cáo", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0",
            padx=3,
            pady=3
        )
        frame_opt.pack(fill="x", padx=5, pady=3)
        
        self.ck_dokho = tk.BooleanVar(value=True)
        self.ck_chatluong = tk.BooleanVar(value=True)
        self.ck_xuhuong = tk.BooleanVar(value=True)
        
        tk.Checkbutton(
            frame_opt, 
            text="Độ khó học phần", 
            variable=self.ck_dokho, 
            bg="#f0f0f0"
        ).pack(anchor="w", pady=1)
        tk.Checkbutton(
            frame_opt, 
            text="Chất lượng giảng dạy", 
            variable=self.ck_chatluong, 
            bg="#f0f0f0"
        ).pack(anchor="w", pady=1)
        tk.Checkbutton(
            frame_opt, 
            text="Xu hướng học tập", 
            variable=self.ck_xuhuong, 
            bg="#f0f0f0"
        ).pack(anchor="w", pady=1)
        
        # 4. Nút Chạy Phân Tích - ĐẶT TRONG SCROLLABLE FRAME
        tk.Button(
            scrollable_frame,
            text="📝 TẠO BÁO CÁO PHÂN TÍCH",
            command=self.generate_report,
            bg="#8e44ad", 
            fg="white",
            font=("Arial", 11, "bold"),
            pady=10
        ).pack(fill="x", padx=5, pady=8)
    
    def create_right_panel(self):
        """Tạo panel hiển thị bên phải"""
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # TAB 1: Dữ liệu
        self.tab_data = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_data, text=" 📋 Dữ liệu Học phần ")
        
        search_df_frame = tk.Frame(self.tab_data, bg="#ecf0f1", height=40)
        search_df_frame.pack(fill="x")
        
        tk.Label(
            search_df_frame, 
            text="🔍 Tìm kiếm trong bảng dữ liệu:", 
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=10, pady=5)
        
        self.entry_filter_df = tk.Entry(search_df_frame, width=40)
        self.entry_filter_df.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_filter_df.bind("<KeyRelease>", self.filter_dataframe_view)
        
        tree_frame = tk.Frame(self.tab_data)
        tree_frame.pack(fill="both", expand=True)
        
        scroll_y = ttk.Scrollbar(tree_frame)
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(
            tree_frame, 
            yscrollcommand=scroll_y.set, 
            xscrollcommand=scroll_x.set,
            selectmode="extended"
        )
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        scroll_y.pack(side=tk.RIGHT, fill="y")
        scroll_x.pack(side=tk.BOTTOM, fill="x")
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        
        # TAB 2: Báo cáo
        self.tab_report = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_report, text=" 📄 Báo cáo Phân tích ")
        
        self.txt_report = tk.Text(
            self.tab_report, 
            font=("Consolas", 11), 
            padx=20, 
            pady=20
        )
        scroll_report = ttk.Scrollbar(
            self.tab_report, 
            command=self.txt_report.yview
        )
        self.txt_report.config(yscrollcommand=scroll_report.set)
        
        scroll_report.pack(side=tk.RIGHT, fill="y")
        self.txt_report.pack(side=tk.LEFT, fill="both", expand=True)
        
        # Định dạng text tags
        self.txt_report.tag_configure(
            "header", 
            font=("Arial", 14, "bold"), 
            foreground="#2980b9"
        )
        self.txt_report.tag_configure(
            "subheader", 
            font=("Arial", 11, "bold"), 
            foreground="#2c3e50"
        )
        self.txt_report.tag_configure("content", font=("Consolas", 11))
        self.txt_report.tag_configure("divider", foreground="#bdc3c7")
    
    # ================= LOGIC XỬ LÝ =================
    
    def load_csv(self):
        """Tải file CSV"""
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        
        try:
            df = load_csv_file(path)
            
            self.df_pandas_original = df.copy()
            self.df_pandas_current = df.copy()
            self.selected_subjects_codes = []
            self.listbox_selected.delete(0, tk.END)
            
            self.show_table(df)
            self.lbl_file_status.config(
                text=f"✓ {os.path.basename(path)} ({len(df)} dòng)", 
                fg="green"
            )
            messagebox.showinfo("Thành công", "Tải dữ liệu thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
    
    def show_table(self, df):
        """Hiển thị dữ liệu lên Treeview"""
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"
        
        for col_name in df.columns:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=100, anchor="center")
        
        for i, (_, row) in enumerate(df.iterrows()):
            if i > 1000: 
                break 
            self.tree.insert("", "end", values=list(row))
    
    def filter_dataframe_view(self, event=None):
        """Tìm kiếm trong dataframe"""
        if self.df_pandas_current is None:
            return
        
        keyword = self.entry_filter_df.get().strip().lower()
        if not keyword:
            self.show_table(self.df_pandas_current)
            return
        
        df_str = self.df_pandas_current.astype(str)
        mask = df_str.apply(
            lambda col: col.str.lower().str.contains(keyword, na=False, regex=False)
        ).any(axis=1)
        
        df_filtered = self.df_pandas_current[mask]
        self.show_table(df_filtered)
    
    def search_subject(self):
        """Tìm kiếm học phần"""
        if self.df_pandas_original is None:
            return
        
        keyword = self.entry_search.get().strip().lower()
        if not keyword:
            return
        
        df = self.df_pandas_original
        filtered = df[
            (df['TenMH'].astype(str).str.lower().str.contains(keyword, na=False)) |
            (df['MaMH'].astype(str).str.lower().str.contains(keyword, na=False))
        ][['MaMH', 'TenMH']].drop_duplicates()
        
        suggestions = [
            f"{row['MaMH']} - {row['TenMH']}" 
            for _, row in filtered.iterrows()
        ]
        self.combo_suggestions['values'] = suggestions
        if suggestions:
            self.combo_suggestions.current(0)
    
    def add_subject_to_list(self):
        """Thêm học phần vào danh sách"""
        ma_mh = None
        ten_mh = None
        
        # Thử lấy từ dòng chọn trong Treeview
        if hasattr(self, "tree"):
            selected_items = self.tree.selection()
            if selected_items:
                item_id = selected_items[0]
                values = self.tree.item(item_id, "values")
                
                if values:
                    columns = list(self.tree["columns"])
                    try:
                        idx_ma = columns.index("MaMH")
                        idx_ten = columns.index("TenMH")
                        ma_mh = str(values[idx_ma]).strip()
                        ten_mh = str(values[idx_ten]).strip()
                    except ValueError:
                        pass
        
        # Fallback về Combobox
        if ma_mh is None:
            selected_text = self.combo_suggestions.get()
            if not selected_text:
                messagebox.showwarning(
                    "Chưa chọn môn",
                    "Hãy chọn một học phần trước."
                )
                return
            parts = selected_text.split(" - ", 1)
            ma_mh = parts[0].strip()
            ten_mh = parts[1].strip() if len(parts) > 1 else ""
        
        # Kiểm tra trùng
        if ma_mh in self.selected_subjects_codes:
            messagebox.showwarning("Trùng lặp", "Môn học này đã có trong danh sách!")
            return
        
        # Thêm vào danh sách
        self.selected_subjects_codes.append(ma_mh)
        display_text = f"{ma_mh} - {ten_mh}" if ten_mh else ma_mh
        self.listbox_selected.insert(tk.END, display_text)
    
    def clear_selection(self):
        """Xóa danh sách chọn"""
        self.selected_subjects_codes = []
        self.listbox_selected.delete(0, tk.END)
        if self.df_pandas_original is not None:
            self.df_pandas_current = self.df_pandas_original.copy()
            self.show_table(self.df_pandas_current)
    
    def generate_report(self):
        """Tạo báo cáo phân tích"""
        if not self.selected_subjects_codes:
            messagebox.showwarning(
                "Cảnh báo",
                "Vui lòng chọn ít nhất một môn học!"
            )
            return
        
        if self.df_pandas_original is None or self.df_pandas_original.empty:
            messagebox.showwarning(
                "Cảnh báo",
                "Chưa có dữ liệu nguồn!"
            )
            return
        
        try:
            # Phân tích bằng Spark
            results = SubjectAnalyzer.analyze_subjects(
                self.df_pandas_original,
                self.selected_subjects_codes
            )
            
            if not results:
                messagebox.showwarning(
                    "Cảnh báo",
                    "Không tìm thấy dữ liệu cho các học phần đã chọn!"
                )
                return
            
            # Tạo báo cáo
            options = {
                "dokho": self.ck_dokho.get(),
                "chatluong": self.ck_chatluong.get(),
                "xuhuong": self.ck_xuhuong.get()
            }
            
            report_lines = SubjectAnalyzer.generate_report_text(results, options)
            
            # Hiển thị báo cáo
            self.txt_report.delete(1.0, tk.END)
            self.notebook.select(self.tab_report)
            
            self.txt_report.insert(
                tk.END,
                "BÁO CÁO PHÂN TÍCH HỌC PHẦN CHI TIẾT\n",
                "header"
            )
            self.txt_report.insert(tk.END, "=" * 50 + "\n\n", "divider")
            
            for line in report_lines:
                self.txt_report.insert(tk.END, line["text"], line["tag"])
            
            messagebox.showinfo("Hoàn tất", "Đã tạo báo cáo thành công!")
            
        except Exception as e:
            messagebox.showerror("Lỗi Phân Tích", str(e))