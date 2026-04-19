import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clustering.load_data import load_data
from src.clustering.transform import transform_to_fact
from src.clustering.feature_engineering import create_features
from src.clustering.model_training import train_model
from src.clustering.evaluation import evaluate

if __name__ == "__main__":
    spark, df = load_data("data/data_demo.csv")
    fact_score = transform_to_fact(df)
    features = create_features(fact_score)
    model, data = train_model(features)
    clusters = evaluate(model, data)
    clusters.show()