from pyspark.sql.functions import expr

def transform_to_fact(df):
    subject_columns = [c for c in df.columns if c not in ["ma_sv", "ho_ten"]]
    stack_expr = "stack({}, {}) as (ma_mon, diem)".format(
        len(subject_columns),
        ",".join([f"'{c}', `{c}`" for c in subject_columns])
    )

    fact_score = df.select(
        "ma_sv",
        expr(stack_expr)
    )

    return fact_score