"""
Xử lý logic phân tích xu hướng nghề nghiệp sinh viên
"""
import pandas as pd

class CareerAnalyzer:
    """
    Class xử lý phân tích xu hướng nghề nghiệp
    """
    
    # Tập luật nghề nghiệp
    CAREER_RULES = {
        "Lập trình viên": ["17206", "17226", "17225", "17522"],
        "Web / Mobile Developer": ["17240", "17423"],
        "Data / AI Engineer": ["17426", "17224"],
        "System / Network Engineer": ["17506", "17203"]
    }
    
    @staticmethod
    def infer_student_job(row, rules=None):
        """
        Suy luận nghề nghiệp phù hợp cho sinh viên
        
        Args:
            row: Series chứa điểm của sinh viên
            rules: Dict quy tắc nghề nghiệp (nếu None sẽ dùng mặc định)
            
        Returns:
            Tên nghề nghiệp phù hợp nhất
        """
        if rules is None:
            rules = CareerAnalyzer.CAREER_RULES
        
        best_job = "Chưa xác định"
        best_score = -1
        
        for job, subjects in rules.items():
            scores = [
                pd.to_numeric(row.get(m), errors="coerce")
                for m in subjects if m in row.index
            ]
            scores = [s for s in scores if pd.notna(s)]
            
            if scores:
                avg = sum(scores) / len(scores)
                if avg > best_score:
                    best_score = avg
                    best_job = job
        
        return best_job
    
    @staticmethod
    def analyze_students(df_student, keyword=""):
        """
        Phân tích xu hướng nghề nghiệp cho danh sách sinh viên
        
        Args:
            df_student: DataFrame chứa điểm sinh viên
            keyword: Từ khóa lọc (tùy chọn)
            
        Returns:
            Tuple (result_df, report_lines)
        """
        df = df_student.copy()
        
        # Lọc theo keyword nếu có
        if keyword:
            mask = df.astype(str).apply(
                lambda col: col.str.lower().str.contains(keyword, na=False, regex=False)
            ).any(axis=1)
            df = df[mask]
        
        if df.empty:
            return None, []
        
        result_rows = []
        report_lines = []
        
        for _, row in df.iterrows():
            ma_sv = row.get("ma_sv", "")
            ho_ten = row.get("ho_ten", "")
            
            best_job = CareerAnalyzer.infer_student_job(row)
            
            # Thêm vào kết quả
            result_rows.append({
                "ma_sv": ma_sv,
                "ho_ten": ho_ten,
                "xu_huong_nghe_nghiep": best_job
            })
            
            # Tạo báo cáo text
            report_lines.append({
                "text": f"Sinh viên: {ho_ten} ({ma_sv})\n",
                "tag": "header"
            })
            report_lines.append({
                "text": "1. Tình hình học tập chung:\n",
                "tag": "sub"
            })
            report_lines.append({
                "text": "- Kết quả học tập nhìn chung ổn định.\n",
                "tag": "content"
            })
            report_lines.append({
                "text": "2. Xu hướng học tập:\n",
                "tag": "sub"
            })
            report_lines.append({
                "text": "- Có xu hướng học tốt các học phần chuyên ngành.\n",
                "tag": "content"
            })
            report_lines.append({
                "text": "3. Định hướng nghề nghiệp đề xuất:\n",
                "tag": "sub"
            })
            report_lines.append({
                "text": f"- Nghề nghiệp phù hợp: {best_job}\n\n",
                "tag": "content"
            })
            report_lines.append({
                "text": "-" * 60 + "\n\n",
                "tag": "divider"
            })
        
        result_df = pd.DataFrame(result_rows)
        
        return result_df, report_lines