from src.clustering.load_data import load_data
from src.clustering.transform import transform_to_fact
from src.clustering.feature_engineering import create_features
from src.clustering.model_training import train_model
from src.clustering.evaluation import evaluate

# 1. Load
spark, df = load_data("data/data_demo.csv")

# 2. Transform
fact_score = transform_to_fact(df)

# 3. Feature
features = create_features(fact_score)

# 4. Train
model, data = train_model(features)

# 5. Evaluate
clusters = evaluate(model, data)
clusters.groupBy("prediction").count().show()
clusters.show()