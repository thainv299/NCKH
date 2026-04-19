import time, re, sys, io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

driver = webdriver.Chrome(options=options)
keyword = 'AI engineer'
driver.get(f'https://topdev.vn/viec-lam-it?q={keyword}')

try:
    print('Waiting for page to load...')
    time.sleep(5)
    page_text = driver.find_element(By.TAG_NAME, 'body').text
    print('Searching patterns...')
    patterns = [
        r'(\d+)\s*việc làm',
        r'(\d+)\s*kết quả',
        r'Tìm thấy\s*(\d+)'
    ]
    for p in patterns:
        matches = re.findall(p, page_text, re.IGNORECASE)
        if matches:
            print(f'Pattern {p} found: {matches}')
except Exception as e:
    print('Error:', e)
finally:
    driver.quit()
