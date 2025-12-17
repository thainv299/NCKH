"""
Cấu hình Spark Session
"""
import os
import sys
from pyspark.sql import SparkSession
from pyspark import SparkConf

# ============================
#  FIX PYTHON VERSION CONFLICT
# ============================
python_executable = sys.executable
os.environ['PYSPARK_PYTHON'] = python_executable
os.environ['PYSPARK_DRIVER_PYTHON'] = python_executable

def create_spark_session():
    """
    Tạo và trả về Spark Session đã cấu hình
    """
    conf = SparkConf() \
        .set("spark.sql.codegen.wholeStage", "false") \
        .set("spark.network.timeout", "1200s") \
        .set("spark.executor.heartbeatInterval", "200s") \
        .set("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .set("spark.python.worker.reuse", "false") \
        .set("spark.executor.memory", "1g") \
        .set("spark.driver.memory", "1g") \
        .set("spark.sql.shuffle.partitions", "1") \
        .set("spark.default.parallelism", "1") \
        .set("spark.rdd.compress", "false") \
        .set("spark.shuffle.compress", "false") \
        .set("spark.shuffle.spill.compress", "false")

    spark = (
        SparkSession.builder
        .appName("HocTapAnalysis_MultiSubject")
        .master("local[1]")
        .config(conf=conf)
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")
    
    return spark

# Tạo Spark session global
spark = create_spark_session()