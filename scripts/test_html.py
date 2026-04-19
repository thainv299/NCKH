import bs4
import re
import json

with open(r'd:\NCKH\src\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = bs4.BeautifulSoup(html, 'lxml')

# Phương pháp 1: Thẻ HTML truyền thống
# TopDev thường dùng thẻ <a> làm wrapper hoặc div class chứa 'job'
h3_titles = []
for h3 in soup.find_all('h3'):
    if h3.text.strip():
        h3_titles.append(h3.text.strip())

print(f"1. HTML Tags (H3): Tìm thấy {len(h3_titles)} tiêu đề")
if h3_titles:
    print(f"   Sample: {h3_titles[:3]}")

# Phương pháp 2: Tìm Data Payload (NextJS __NEXT_DATA__ hoặc JSON nhúng)
next_data = soup.find('script', id='__NEXT_DATA__')
print(f"2. Next.js ID=__NEXT_DATA__: {'CO' if next_data else 'KHONG_CO'}")

# Phương pháp 3: Tìm Regex Stringified Titles (Vì TopDev giấu Job trong thuộc tính JSON payload của NextJS)
title_matches = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
print(f"3. Regex JSON Payload: Tìm thấy {len(title_matches)} tiêu đề")
if title_matches:
    print(f"   Sample: {(list(set(title_matches)))[:3]}")
