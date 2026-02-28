"""
Các hàm tiện ích xử lý dữ liệu
"""
import pandas as pd
from pyspark.sql.functions import col, when

def normalize_columns(df):
    """
    Chuẩn hóa tên cột - xóa khoảng trắng
    """
    rename_map = {}
    for col_name in df.columns:
        new_col = col_name.replace(" ", "").replace("%", "%")
        rename_map[col_name] = new_col
    return df.rename(columns=rename_map)
def detect_delimiter(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()

    if first_line.count(";") > first_line.count(","):
        return ";"
    else:
        return ","

def load_csv_file(file_path):
    """
    Đọc file CSV với:
    - Tự động detect delimiter
    - Tự động fallback encoding
    """
    sep = detect_delimiter(file_path)

    try:
        df = pd.read_csv(file_path, encoding="utf-8", sep=sep)
    except:
        try:
            df = pd.read_csv(file_path, encoding="latin1", sep=sep)
        except Exception as e:
            raise Exception(f"Không thể đọc file: {str(e)}")

    return normalize_columns(df)

def validate_required_columns(df, required_cols):
    """
    Kiểm tra các cột bắt buộc có tồn tại không
    """
    missing = [c for c in required_cols if c not in df.columns]
    return missing
def convert_to_4_scale(column):
    return (
        when((col(column) >= 9.0) & (col(column) <= 10.0), 4.0)
        .when((col(column) >= 8.5) & (col(column) < 9.0), 4.0)
        .when((col(column) >= 8.0) & (col(column) < 8.5), 3.5)
        .when((col(column) >= 7.0) & (col(column) < 8.0), 3.0)
        .when((col(column) >= 6.5) & (col(column) < 7.0), 2.5)
        .when((col(column) >= 5.5) & (col(column) < 6.5), 2.0)
        .when((col(column) >= 5.0) & (col(column) < 5.5), 1.5)
        .when((col(column) >= 4.0) & (col(column) < 5.0), 1.0)
        .otherwise(0.0)
    )