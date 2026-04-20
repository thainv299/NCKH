import tkinter as tk
from tkinter import ttk

class LoadingOverlay:
    """
    Lớp phủ mờ giao diện với thông báo đang xử lý.
    """
    def __init__(self, parent, text="Đang xử lý dữ liệu..."):
        self.parent = parent
        self.text = text
        self.overlay = None
        self.bind_id = None
        
    def show(self):
        """Hiển thị lớp phủ"""
        if self.overlay:
            return
            
        # Tạo toplevel không có khung (overrideredirect)
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-alpha", 0.7)  # Độ trong suốt
        self.overlay.configure(bg="#1e293b")   # Màu tối (Slate 900)
        
        # Căn chỉnh overlay trùm lên parent
        self.update_position()
        
        # Thông báo
        container = tk.Frame(self.overlay, bg="#1e293b")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Icon giả lập spinner (emoji)
        self.spinner_label = tk.Label(
            container, text="⏳", 
            font=("Segoe UI Emoji", 32), 
            bg="#1e293b", fg="#3b82f6"
        )
        self.spinner_label.pack(pady=10)
        
        tk.Label(
            container, text=self.text, 
            font=("Segoe UI", 14, "bold"), 
            bg="#1e293b", fg="white"
        ).pack(pady=5)
        
        tk.Label(
            container, text="Vui lòng đợi trong giây lát", 
            font=("Segoe UI", 10), 
            bg="#1e293b", fg="#94a3b8"
        ).pack()

        # Binding để cập nhật vị trí khi parent di chuyển/resize
        # Sử dụng add='+' để không ghi đè các binding khác của parent
        self.bind_id = self.parent.bind("<Configure>", self.update_position_event, add="+")
        
    def update_position_event(self, event):
        self.update_position()

    def update_position(self):
        if not self.overlay or not self.parent.winfo_exists():
            return
        try:
            x = self.parent.winfo_rootx()
            y = self.parent.winfo_rooty()
            w = self.parent.winfo_width()
            h = self.parent.winfo_height()
            self.overlay.geometry(f"{w}x{h}+{x}+{y}")
        except:
            pass

    def hide(self):
        """Ẩn lớp phủ"""
        if self.overlay:
            if self.bind_id and self.parent.winfo_exists():
                try:
                    self.parent.unbind("<Configure>", self.bind_id)
                except:
                    pass
            self.overlay.destroy()
            self.overlay = None
            self.bind_id = None
