import pandas as pd
import numpy as np
import random
import math
num_students = 1000   
output_file = "data_demo_1.csv"

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
    group = random.choices(
        ["xuat_sac", "kha", "trung_binh", "nguy_hiem"],
        weights=[0.2, 0.3, 0.3, 0.2]
    )[0]

    for subject in subjects:

        if group == "xuat_sac":
            score = np.random.normal(8.8, 0.4)

        elif group == "kha":
            score = np.random.normal(7.5, 0.6)

        elif group == "trung_binh":
            score = np.random.normal(6.0, 0.8)

        else:  # nguy_hiem
            # 40% khả năng trượt môn
            if random.random() < 0.4:
                score = np.random.normal(3.5, 0.5)
            else:
                score = np.random.normal(5.0, 0.8)

        score = max(0, min(10, score))
        score = round(score, 1)

        row[subject] = score

    data.append(row)

df_demo = pd.DataFrame(data)
df_demo.to_csv(output_file, sep=";", index=False)
print("Đã tạo xong file:", output_file)
print("Kích thước dữ liệu:", df_demo.shape)
print(df_demo.head())