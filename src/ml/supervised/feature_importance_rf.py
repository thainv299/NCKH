from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

class RandomForestFeatureExtractor:
    @staticmethod
    def extract_important_subjects(df, feature_prefixes=("_", "_4"), label_col="nhom_san_sang", num_trees=10, max_depth=5):
        """
        Trích xuất top các môn học quan trọng nhất giúp phân loại sinh viên
        bằng thuật toán Random Forest Classifier.
        """
        # Auto-detect subject columns based on prefixes
        score_cols = [c for c in df.columns if c.startswith(feature_prefixes[0]) and c.endswith(feature_prefixes[1])]
        if not score_cols or label_col not in df.columns:
            return []

        indexer = StringIndexer(inputCol=label_col, outputCol="ml_label")
        for c in score_cols:
            df = df.withColumn(c, F.coalesce(F.col(c).cast(DoubleType()), F.lit(0.0)))

        assembler = VectorAssembler(inputCols=score_cols, outputCol="dt_features")
        rf = RandomForestClassifier(featuresCol="dt_features", labelCol="ml_label", numTrees=num_trees, maxDepth=max_depth)

        try:
            df_indexed = indexer.fit(df).transform(df)
            df_assembled = assembler.transform(df_indexed)
            
            # Huấn luyện
            rf_model = rf.fit(df_assembled)

            # Lấy độ quan trọng
            importances = rf_model.featureImportances.toArray()
            result = []
            for i, col_name in enumerate(score_cols):
                subject_code = col_name.replace("_", "").replace("4", "")
                if i < len(importances) and importances[i] > 0.01:
                    result.append((subject_code, round(float(importances[i]) * 100, 1)))
                    
            # Sắp xếp giảm dần theo phần trăm đóng góp
            result.sort(key=lambda x: x[1], reverse=True)
            return result[:10]
        except Exception as e:
            print(f"RandomForest Error: {e}")
            return []
