import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pyspark.sql import SparkSession
from src.utils.data_utils import load_csv_file
from src.services.student_predictor import StudentPredictorService


class StudentPredictionTab:

    def __init__(self, parent):
        self.parent = parent
        self.spark = None
        self.df_student = None
        self.create_layout()

    def get_spark(self):
        if self.spark is None:
            self.spark = SparkSession.builder \
                .appName("Student Prediction") \
                .master("local[*]") \
                .getOrCreate()
        return self.spark

    def create_layout(self):

        tk.Button(
            self.parent,
            text="Load CSV & Predict",
            command=self.load_and_predict,
            bg="#2980b9",
            fg="white",
            pady=8
        ).pack(fill="x", padx=10, pady=10)

        self.tree = ttk.Treeview(self.parent)
        self.tree.pack(fill="both", expand=True)

    def load_and_predict(self):

        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return

        try:
            spark = self.get_spark()
            spark_df = load_csv_file(spark, path)

            result = StudentPredictorService.predict_students(
                spark_df,
                spark
            )

            # show result as pandas for Treeview
            result_pd = result.limit(2000).toPandas()
            self.show_table(result_pd)

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def show_table(self, df):

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"

        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # Style tag
        self.tree.tag_configure("danger", background="#f8d7da")
        self.tree.tag_configure("warning", background="#fff3cd")
        self.tree.tag_configure("good", background="#ffffff")
        self.tree.tag_configure("excellent", background="#c3e6cb")

        for _, row in df.iterrows():

            cluster = row["prediction"]

            if cluster == 2:
                tag = "danger"
            elif cluster == 0:
                tag = "warning"
            elif cluster == 3:
                tag = "good"
            else:
                tag = "excellent"

            self.tree.insert("", "end", values=list(row), tags=(tag,))