import os
import gc
import time
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# 세종 크롤링 코드

driver.get("https://www.shinkim.com/kor/member")
driver.maximize_window()
time.sleep(1)

company = "세종"

categories = driver.find_elements(By.XPATH, '//*[@id="bizCode"]/option')
pf_data = []
for category in tqdm.tqdm(range(2, len(categories)+1)):
    # 뒤에서 page 넘길 때 사용하는 page_number
    page_num = 1
    # 카테고리 선택
    category_box = driver.find_element(By.XPATH, f'//*[@id="bizCode"]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_box) # 카테고리 박스로 스크롤
    driver.execute_script("arguments[0].click();", category_box) # 카테고리 박스 클릭
    time.sleep(0.5)
    cate = category_box.find_element(By.XPATH, f'.//option[{category}]')
    # driver.execute_script("arguments[0].click();", cate) # 카테고리 선택
    cate.click()
    print("-----", cate.text, "-----")
    time.sleep(0.5)
    search_button = driver.find_element(By.CSS_SELECTOR, "button.btn.theme-b.type-a.rise-03")
    driver.execute_script("arguments[0].click();", search_button) # 검색 버튼 클릭
    time.sleep(3)

    while True:
        # 주요구성원, 구성원 상관없이 화면에 뜨는 모든 pf 정보 가져옴
        pf_lst = driver.find_elements(By.CSS_SELECTOR, 'li.data-item') # 구성원 리스트
        for pf in pf_lst:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pf) # 크롤링 pf로 화면 스크롤
            time.sleep(2)
            pf_name = pf.find_element(By.CSS_SELECTOR, 'a.text')
            name = pf_name.text
            job = pf.find_element(By.CSS_SELECTOR, 'span.sort').text
            call = pf.find_element(By.CSS_SELECTOR, 'span.info-item.telephone').text

            if check_duplicates(name, job, call):
                print(name, job, call)
                driver.execute_script("arguments[0].click();", pf_name)
                time.sleep(3)

                # 관련 분야
                fields_lst = driver.find_elements(By.CSS_SELECTOR, 'ul.related-work li')
                fields_total = []
                for field in fields_lst:
                    fields_total.append(field.text)
                related_fields = ','.join(fields_total)
                time.sleep(2)

                # 경력
                wait = WebDriverWait(driver, 10)
                career_box = wait.until(EC.presence_of_element_located((By.ID, "professionalCareer")))
                title = career_box.find_element(By.CSS_SELECTOR, 'h5.subsection-name').text
                # 경력 더보기 버튼 존재 시 클릭
                while True:
                    try:
                        career_button = career_box.find_element(By.CSS_SELECTOR, 'button span.open')
                        driver.execute_script("arguments[0].click();", career_button)
                        time.sleep(1)
                    except:
                        break
                career_lst = career_box.find_elements(By.CSS_SELECTOR, 'div.data-list-area li.data-item')
                career_total = []
                for careers in career_lst:
                    period = careers.find_element(By.CSS_SELECTOR, 'span.data-head').text
                    content = careers.find_element(By.CSS_SELECTOR, 'span.data-body').text
                    career_total.append(f'{content} ({period})')
                career = ','.join(career_total)
                time.sleep(2)

                # 학력, 자격, 수상
                detail_table = driver.find_elements(By.CSS_SELECTOR, 'div#keyExperience div.subsection')
                eligibility, awards = "", ""
                for detail in detail_table:
                    detail_title = detail.find_element(By.CSS_SELECTOR, 'h5.subsection-name').text
                    # 외부 평가
                    assessment_flag = False
                    if detail_title == "외부 평가":
                        assessment_flag = True

                    if detail_title in ["학력", "자격", "수상 내역", "외부 평가"]:
                        while True:
                            try:
                                button = detail.find_element(By.CSS_SELECTOR, 'button span.open')
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(2)
                            except:
                                break
                        detail_contents = detail.find_elements(By.CSS_SELECTOR, 'div.data-list-area li.data-item')
                        box_total = []
                        for detail_content in detail_contents:
                            try:
                                period = detail_content.find_element(By.CSS_SELECTOR, 'span.data-head').text
                            except:
                                period = ""
                            content = detail_content.find_element(By.CSS_SELECTOR, 'span.data-body').text
                            if assessment_flag or not period:
                                box_total.append(content)
                            else:
                                box_total.append(f'{content} ({period})')

                        if detail_title == "학력":
                            education = ','.join(box_total)
                        elif detail_title == "자격":
                            eligibility = ','.join(box_total)
                        elif detail_title == "수상 내역":
                            awards = ','.join(box_total)
                        else:
                            assessment = ','.join(box_total)


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
                            'assessment':assessment
                        }
                pf_data.append(add_pf)
                driver.back()
                time.sleep(3)
        
        # 페이지가 넘어갈 수 있으면 다음 페이지로 이동, 더이상 넘어갈 페이지가 없으면 while문 break
        try:
            exist_next = driver.find_element(By.CSS_SELECTOR, 'span.direction a.next')
            if exist_next: # 다음으로 넘어갈 페이지가 있으면
                page_num += 1
                pagination = driver.find_element(By.CSS_SELECTOR, 'span.pagination')
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination)
                click_page = pagination.find_element(By.XPATH, f'.//a[{page_num}]')
                driver.execute_script("arguments[0].click();", click_page)
                time.sleep(2)
            else:
                break
        except:
            break
    # 카테고리 하나당 한번씩 df 갱신
    df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)

today_folder = datetime.now().strftime("%Y-%m-%d")
os.makedirs(f"data/{today_folder}", exist_ok=True)

today = datetime.now().strftime("%y%m%d")
df.to_csv(f"data/{today_folder}/Shin_Kim_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()