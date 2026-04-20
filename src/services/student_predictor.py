from pyspark.ml.clustering import KMeansModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import functions as F
from functools import reduce
from pyspark.sql.functions import when, col
from src.utils.data_utils import convert_to_4_scale

class StudentPredictorService:

    @staticmethod
    def predict_students(spark_df, spark, model_path=None):
        from src.ml.unsupervised.risk_clustering import RiskClustering
        
        # ML Logic has been delegated to src/ml component
        result_df = RiskClustering.cluster(spark_df, model_path=model_path)
        return result_df