import os
import gc
import time
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import tqdm
from selenium import webdriver
from selenium.webdriver.common. by import By
from datetime import datetime

# --- Github 환경 추가 라이브러리 ---
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

gc.collect()

options = Options()
options.add_argument("--headless")           # 브라우저 창을 띄우지 않음 (필수)
options.add_argument("--no-sandbox")          # 보안 기능 해제 (리눅스 서버 필수)
options.add_argument("--disable-dev-shm-usage") # 공유 메모리 부족 방지
options.add_argument("--disable-gpu")         # GPU 가속 해제
options.add_argument("--window-size=1920,1080") # 가상 모니터 크기 설정 (스크롤/클릭 오류 방지)

# 데이터 프레임 정의
col = ['company','name','job','call','related_fields','career','education','eligibility','awards','assessment']
df = pd.DataFrame(columns=col)
# 회사명, 이름, 직업, 전화번호, 업무분야, 경력, 학력, 자격, 수상, 외부평가(세종에만 있음)

exist_data = set()

# 중복 확인용 함수
def check_duplicates(name, job, call):
    global exist_data
    new = (name, job, call)
    if new in exist_data:
        return False
    else:
        exist_data.add(new)
        return True
    
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 화우 크롤링 코드

driver.get("https://www.hwawoo.com/kor/professionals/members?lang=ko")
driver.maximize_window()
time.sleep(3)
search_button = driver.find_element(By.CSS_SELECTOR, '#container > div.lawyer-search-wrap > div > div.box-input-wrap.with-select > div.box-input.ty-search > button.icon-search-big')
driver.execute_script("arguments[0].click();", search_button)
time.sleep(1)

# 더보기 버튼 모두 클릭
while True:
    button = driver.find_element(By.XPATH, '//*[@id="moreButton"]/button')
    driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", button)
    time.sleep(1)
    if button.is_displayed():
        button.click()
    else:
        break

company = "화우"

pf_lst = driver.find_elements(By.XPATH, '//*[@id="contentsList"]/div')
pf_data = []
for i in tqdm.tqdm(1, range(len(pf_lst))+1):
    pf = driver.find_elements(By.XPATH, f'//*[@id="contentsList"]/div[{i}]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", pf) # 크롤링 pf로 화면 스크롤
    time.sleep(1)
    name = pf.find_element(By.CSS_SELECTOR, 'strong.name').text
    job = pf.find_element(By.CSS_SELECTOR, 'span.grade').text
    call = '-'.join(pf.find_element(By.CSS_SELECTOR, 'span.tel').text.split())

    if check_duplicates(name, job, call):
        print(name, job, call)
        pf.click()
        time.sleep(3)
        
        # 관련분야, 경력, 학력, 자격, 수상
        detail_table = driver.find_elements(By.CSS_SELECTOR, 'div.tab-wrap.box-detail-contents.tab-ctrl article[id^="anchor_cont_"]')
        eligibility, awards = "", ""
        for detail in detail_table:
            detail_title = detail.find_element(By.XPATH, './/div[1]/h3').text
            
            if detail_title in ["업무분야", "경력", "학력", "자격", "수상"]:
                while True:
                    try:
                        button = detail.find_element(By.XPATH, './/div[2]/button')
                        if button.is_displayed() and button.text == "더보기":
                            button.click()
                        else:
                            break
                    except:
                        break
                detail_contents = detail.find_elements(By.CSS_SELECTOR, 'ul.dot-list li')
                box_total = []
                for detail_content in detail_contents:
                    content = detail_content.text
                    if detail_title in ["경력", "학력"]:
                        period, cont = content.split('\n')
                        box_total.append(f'{cont} ({period})')
                    else:
                        box_total.append(content)
                # 자격의 경우, 리스트 형식일 때도 있고 아닐 때도 있어서
                # 리스트 형식이 아니어서 저장이 안되었을 경우에 대한 if문
                if detail_title == "자격" and not len(detail_contents):
                    content = detail.find_element(By.XPATH, './/div[2]/div').text
                    box_total.append(content)

                if detail_title == "업무분야":
                    related_fields = ','.join(box_total)
                elif detail_title == "경력":
                    career = ','.join(box_total)
                elif detail_title == "학력":
                    education = ','.join(box_total)
                elif detail_title == "자격":
                    eligibility = ','.join(box_total)
                else:
                    awards = ','.join(box_total)

        add_pf = {
                    'company':company,
                    'name':name,
                    'job':job,
                    'call':call,
                    'related_fields':related_fields,
                    'career':career,
                    'education':education,
                    'eligibility':eligibility,
                    'awards':awards,
                    'assessment':""
                }
        pf_data.append(add_pf)

        driver.back()
        time.sleep(3)

# 카테고리 하나당 한번씩 df 갱신
df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)

today_folder = datetime.now().strftime("%Y-%m-%d")
os.makedirs(f"data/{today_folder}", exist_ok=True)

today = datetime.now().strftime("%y%m%d")
df.to_csv(f"data/{today_folder}/Hwawoo_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()