import requests
import csv
import os

API_URL = "https://api.topdev.vn/td/v2/job-categories/job-category-with-all-type?locale=vi_VN"

def fetch_macro_market_data():
    print("Dang lay du lieu thi truong tu TopDev API (Macro Level)...")
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        categories = data.get("data", [])
        
        job_stats = []
        for cat in categories:
            cat_name = cat.get("name", "Unknown")
            
            # Chỉ lấy dữ liệu chuyên ngành IT
            if cat_name != "IT":
                continue
                
            roles = cat.get("roles", [])
            if not roles:
                # Nếu không có roles con, ghi nhận tổng ngành
                job_stats.append({
                    "Category": cat_name,
                    "Role": cat_name, 
                    "JobCount": cat.get("job_count", 0)
                })
            else:
                for role in roles:
                    job_stats.append({
                        "Category": cat_name,
                        "Role": role.get("name", "Unknown"),
                        "JobCount": role.get("job_count", 0)
                    })
        return job_stats
    except Exception as e:
        print(f"Loi truy cap API: {e}")
        return []

def main():
    job_stats = fetch_macro_market_data()
    
    if not job_stats:
        print("Cảnh báo: Không lấy được dữ liệu.")
        return
        
    # Tính đường dẫn tuyệt đối cho output
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "input", "real_jobs.csv"
    )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Category", "Role", "JobCount"])
        writer.writeheader()
        writer.writerows(job_stats)
        
    print(f"\nDONE! Da luu {len(job_stats)} chuyen nganh vao {output_path}")

if __name__ == "__main__":
    main()
