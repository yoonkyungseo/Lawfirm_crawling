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
# 태평양 크롤링 코드

driver.get("https://www.bkl.co.kr/law/member/allList.do?isMain=&pageIndex=1&searchCondition=&url=all&job=&lang=ko&memberNo=&searchYn=Y&logFunction=goSearch&searchKeyword=")
driver.maximize_window()
time.sleep(1)

company = "태평양"

# 주요 구성원 id = isMainY, button_id = 2
# 관련 구성원 id = isMainN, button_id = 3
# button_id는 "더보기 버튼" 클릭 시 XPATH 내 달라지는 div 리스트 넘버
def bkl_crawling(id, button_id):
    global company, df
    page = 1
    while True:
        pf_data = []
        scroll = driver.find_element(By.XPATH, f'//*[@id="{id}"]/ul[{page}]/li[1]/a[1]/div[1]')
        driver.execute_script("arguments[0].scrollIntoView(true);", scroll)
        time.sleep(1)

        pf_lst = driver.find_elements(By.XPATH, f'//*[@id="{id}"]/ul[{page}]/li')
        for i in range(1,len(pf_lst)+1):
            pf = driver.find_element(By.XPATH, f'//*[@id="{id}"]/ul[{page}]/li[{i}]/a[1]')
            # 이름, 직업, 전화번호
            name = pf.find_element(By.XPATH, './/div[2]').text
            job = pf.find_element(By.XPATH, './/div[3]').text
            call = pf.find_element(By.XPATH, './/div[5]').text.replace('T.','')
            print(name, job, call)
            # 자격, 수상 없는 경우를 대비하여 기본값 설정
            eligibility, awards = "", ""
            
            # 해당 pf가 기존에 저장된 사람인지 확인
            if check_duplicates(name, job, call):
                pf.click()
                time.sleep(3)

                # 관련 분야
                fields_lst = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/div[2]/div/div[1]/ul/li')
                fields_total = []
                for field in fields_lst:
                    fields_total.append(field.text)
                related_fields = ','.join(fields_total)
                
                sections = driver.find_elements(By.CSS_SELECTOR, '.prof-section.ui-scroll-spy-section.ui-box')
                for section in sections:
                    title_ = section.find_element(By.CLASS_NAME, "prof-title")
                    title = title_.text.strip()
                    # 경력, 학력, 자격취득
                    if title in ["경력", "학력", "자격취득"]:
                        box_lst = section.find_elements(By.XPATH, './/div[2]/div/div')
                        box_total = []
                        for box in box_lst:
                            content = box.find_element(By.XPATH, './/span[2]').text
                            period = box.find_element(By.XPATH, './/span[1]').text
                            box_total.append(f'{content} ({period})')
                        if title == "경력":
                            career = ','.join(box_total)
                        elif title == "학력":
                            education = ','.join(box_total)
                        else:
                            eligibility = ','.join(box_total)
                    # 수상
                    elif "주요활동" in title:
                        title_.find_element(By.XPATH, './/button').click()
                        try:
                            awards_title = section.find_element(By.XPATH, ".//div[normalize-space()='수상']")
                            awards_lst = awards_title.find_elements(By.XPATH, './/following-sibling::div')
                            award_total = []
                            for award in awards_lst:
                                award_total.append(award.text)
                            awards = ','.join(award_total)
                        except:
                            awards = ""

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
                time.sleep(4)
        # 더보기 버튼 클릭 전마다 df 갱신
        df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)

        try:
            button = driver.find_element(By.XPATH, f'//*[@id="{id}"]/div[{button_id}]/button')
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", button)
            button.click()
            time.sleep(2)
            driver.refresh()
            time.sleep(4)
            page += 1
        except:
            break

bkl_crawling("isMainY", 2)
bkl_crawling("isMainN", 3)

today_folder = datetime.now().strftime("%Y-%m-%d")
os.makedirs(f"data/{today_folder}", exist_ok=True)

today = datetime.now().strftime("%y%m%d")
df.to_csv(f"BKL_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()