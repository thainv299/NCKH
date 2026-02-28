"""
Các hàm tiện ích xử lý dữ liệu
"""
import pandas as pd
from pyspark.sql.functions import col, when

def normalize_columns_spark(sdf):
    """
    Chuẩn hóa tên cột cho Spark DataFrame
    """
    for col_name in sdf.columns:
        new_col = col_name.replace(" ", "").replace("%", "%")
        if new_col != col_name:
            sdf = sdf.withColumnRenamed(col_name, new_col)
    return sdf
def detect_delimiter(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()

    if first_line.count(";") > first_line.count(","):
        return ";"
    else:
        return ","

def load_csv_file(spark, file_path):
    """
    Đọc CSV bằng Spark:
    - Tự động detect delimiter
    - inferSchema
    - chuẩn hóa cột
    """
    sep = detect_delimiter(file_path)

    sdf = (
        spark.read
             .option("header", True)
             .option("inferSchema", True)
             .option("delimiter", sep)
             .csv(file_path)
    )

    sdf = normalize_columns_spark(sdf)
    return sdf

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