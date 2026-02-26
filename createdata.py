import pandas as pd
import numpy as np
import random
import math
num_students = 1000   
output_file = "data_demo.csv"

subjects = [
    '11401','17102','17103','17200','17222','11124','17206','17202',
    '17204','17426','18101','24102','24103','24202','29101','17223',
    '17226','17422','17506','17542','18401','17212','17203','17225',
    '17427','17522','19201','17224','17201','17214','17434','17221',
    '17227','17240','17423','19202','25101'
]

data = []

for i in range(num_students):
    ma_sv = f"SV{i:05d}"
    ho_ten = f"SinhVien_{i}"

    row = {
        "ma_sv": ma_sv,
        "ho_ten": ho_ten
    }
    group = random.choice(["gioi", "tb", "yeu"])

    for subject in subjects:
        if group == "gioi":
            score = np.random.normal(8.5, 0.7)
        elif group == "tb":
            score = np.random.normal(6.5, 1.0)
        else:
            score = np.random.normal(4.5, 1.2)

        score = round(max(0, min(10, score)), 2)
        score = math.ceil(score * 10) / 10
        row[subject] = score
    data.append(row)

df_demo = pd.DataFrame(data)
df_demo.to_csv(output_file, sep=";", index=False)
print("Đã tạo xong file:", output_file)
print("Kích thước dữ liệu:", df_demo.shape)
print(df_demo.head())