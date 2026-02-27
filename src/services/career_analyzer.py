from pyspark.sql import functions as F


class CareerAnalyzerSpark:

    CAREER_RULES = {
        "Kỹ thuật phần mềm": [
            "17206", "17236", "17523",
            "17335", "17432", "17427", "17314"
        ],
        "Web & Mobile Developer": [
            "17340", "17523", "17434", "17423"
        ],
        "Data / Backend Engineer": [
            "17236", "17426", "17233", "17434", "17427"
        ],
        "AI / Xử lý ảnh": [
            "17234", "17221", "17233", "17104"
        ],
        "Mạng & An toàn thông tin": [
            "17506", "17212", "17303", "17304"
        ],
        "Hệ thống nhúng & IoT": [
            "17302", "17301", "17337", "17304"
        ]
    }

    @staticmethod
    def analyze_students(df_student, keyword=""):

        df = df_student

        # ==========================
        # LỌC THEO KEYWORD
        # ==========================
        if keyword:
            cond = None
            for c in df.columns:
                expr = F.lower(F.col(c).cast("string")).contains(keyword.lower())
                cond = expr if cond is None else (cond | expr)
            df = df.filter(cond)

        if df.count() == 0:
            return None
        # ==========================
        # ==========================
        score_cols = {}

        for career, subjects in CareerAnalyzerSpark.CAREER_RULES.items():
            cols = [
                F.col(s).cast("double")
                for s in subjects
                if s in df.columns
            ]

            if cols:
                avg = sum(cols) / F.lit(len(cols))
            else:
                avg = F.lit(None)

            col_name = career.replace(" ", "_").replace("/", "_")
            df = df.withColumn(col_name, avg)
            score_cols[career] = col_name

        # ==========================
        # SUY LUẬN NGÀNH PHÙ HỢP
        # ==========================
        max_score = F.greatest(*[
            F.col(c) for c in score_cols.values()
        ])

        df = df.withColumn("max_score", max_score)

        df = df.withColumn(
            "nganh_phu_hop",
            F.when(F.col(score_cols["Kỹ thuật phần mềm"]) == max_score, "Kỹ thuật phần mềm")
             .when(F.col(score_cols["Web & Mobile Developer"]) == max_score, "Web & Mobile Developer")
             .when(F.col(score_cols["Data / Backend Engineer"]) == max_score, "Data / Backend Engineer")
             .when(F.col(score_cols["AI / Xử lý ảnh"]) == max_score, "AI / Xử lý ảnh")
             .when(F.col(score_cols["Mạng & An toàn thông tin"]) == max_score, "Mạng & An toàn thông tin")
             .when(F.col(score_cols["Hệ thống nhúng & IoT"]) == max_score, "Hệ thống nhúng & IoT")
             .otherwise("Chưa xác định")
        )

        return df.select(
            "ma_sv",
            "ho_ten",
            "nganh_phu_hop"
        )
