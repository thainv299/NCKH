"""
Cửa sổ chính của ứng dụng
"""
import tkinter as tk
from tkinter import ttk
from gui.subject_tab import SubjectAnalysisTab
from gui.career_tab import CareerAnalysisTab

class MainWindow:
    """
    Class quản lý cửa sổ chính và các tab
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Báo cáo Phân tích")
        self.root.geometry("1200x750")
        
        # Cấu hình style
        self.setup_style()
        
        # Tạo notebook chính
        self.notebook_main = ttk.Notebook(self.root)
        self.notebook_main.pack(fill="both", expand=True)
        
        # Tạo các tab
        self.create_tabs()
    
    def setup_style(self):
        """Cấu hình style cho ttk"""
        style = ttk.Style()
        style.theme_use("clam")
    
    def create_tabs(self):
        """Tạo các tab chính"""
        # Tab 1: Phân tích học phần
        self.tab_subject = tk.Frame(self.notebook_main)
        self.notebook_main.add(self.tab_subject, text="Phân tích Học phần")
        self.subject_analysis = SubjectAnalysisTab(self.tab_subject)
        
        # Tab 2: Phân tích xu hướng nghề nghiệp
        self.tab_career = tk.Frame(self.notebook_main)
        self.notebook_main.add(self.tab_career, text="Xu hướng Nghề nghiệp SV")
        self.career_analysis = CareerAnalysisTab(self.tab_career)