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

# 광장 크롤링 코드

driver.get("https://www.leeko.com/leenko/member/memberList.do?lang=KR")
driver.maximize_window()
time.sleep(1)

company = "광장"

categories = driver.find_elements(By.XPATH, '//*[@id="mCSB_2_container"]/li')
pf_data = []
for category in tqdm.tqdm(range(2, len(categories)+1)):
    # 카테고리 선택
    category_box = driver.find_element(By.XPATH, "//div[@class='leeko-member-search__select']//div[@class='nice-select chosen-select']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_box) # 카테고리 박스로 스크롤
    category_box.click() # 카테고리 박스 클릭
    cate = driver.find_element(By.XPATH, f'//*[@id="mCSB_2_container"]/li[{category}]')
    print("-----", cate.text, "-----")
    cate.click() # 카테고리 선택
    driver.find_element(By.XPATH, "//div[@class='leeko-member-search__form']/button").click() # 검색 버튼 클릭
    time.sleep(3)

    # 모든 더보기 버튼 클릭해서 화면에 pf 정보가 다 뜨도록 설정
    while True:
        try:
            button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[6]/a/strong')
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", button)
            time.sleep(1)
            button.click()
        except:
            break

    category_member_lst = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[5]/div') # 구성원 리스트
    pf_lines = category_member_lst.find_elements(By.CSS_SELECTOR, "div.leeko-member__list") # 구성원 리스트에서 한 줄씩 뽑기

    for pf_line in pf_lines:
        pf_lst = pf_line.find_elements(By.XPATH, './/a')
        for pf in pf_lst:
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", pf) # 크롤링 pf로 화면 스크롤
            name = pf.find_element(By.XPATH, './/div[2]/strong/span').text
            job = pf.find_element(By.XPATH, './/div[2]/p').text
            call = pf.find_element(By.XPATH, './/div[3]/p[1]').text.split('\n')[1]
            print(name, job, call)

            if check_duplicates(name, job, call):
                pf.click()
                time.sleep(3)

                # 관련 분야
                fields_lst = driver.find_elements(By.CSS_SELECTOR, '.leeko-tag.leeko-tag--dark a')
                fields_total = []
                for field in fields_lst:
                    fields_total.append(field.text)
                related_fields = ','.join(fields_total)

                # 경력, 학력, 자격, 수상
                detail_table = driver.find_elements(By.CSS_SELECTOR, '.leeko-member-detail__table')
                eligibility, awards = "", ""
                for detail in detail_table:
                    detail_title = detail.find_element(By.XPATH, './/div[1]').text

                    if detail_title in ["경력", "학력", "자격/회원", "수상실적"]:
                        try:
                            button = detail.find_element(By.XPATH, './/a')
                            while True:
                                if button.text == "더보기":
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", button)
                                    button.click()
                                else:
                                    break
                        except:
                            pass
                        detail_contents = detail.find_elements(By.XPATH, './/div[2]//tr')
                        box_total = []
                        for detail_content in detail_contents:
                            period = detail_content.find_element(By.XPATH, './/th').text
                            content = detail_content.find_element(By.XPATH, './/td').text
                            box_total.append(f'{content} ({period})')

                        if detail_title == "경력":
                            career = ','.join(box_total)
                        elif detail_title == "학력":
                            education = ','.join(box_total)
                        elif detail_title == "자격/회원":
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
df.to_csv(f"Lee_Ko_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()