"""
Các hàm tiện ích xử lý dữ liệu
"""
import pandas as pd

def normalize_columns(df):
    """
    Chuẩn hóa tên cột - xóa khoảng trắng
    """
    rename_map = {}
    for col_name in df.columns:
        new_col = col_name.replace(" ", "").replace("%", "%")
        rename_map[col_name] = new_col
    return df.rename(columns=rename_map)

def load_csv_file(file_path):
    """
    Đọc file CSV với encoding tự động
    """
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except:
        try:
            df = pd.read_csv(file_path, encoding="latin1")
        except Exception as e:
            raise Exception(f"Không thể đọc file: {str(e)}")
    
    return normalize_columns(df)

def validate_required_columns(df, required_cols):
    """
    Kiểm tra các cột bắt buộc có tồn tại không
    """
    missing = [c for c in required_cols if c not in df.columns]
    return missing