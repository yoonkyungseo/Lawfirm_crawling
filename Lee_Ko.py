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
import glob

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

base_path = 'data'
try:
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    folders.sort()
    latest_folder = folders[-2] # 가장 최근 폴더 선택
    old_csv_files = glob.glob(os.path.join(f'data/{latest_folder}', "Lee_Ko*.csv"))
    if old_csv_files:
        print("참고할 이전 파일을 찾았습니다.")
        df_old = pd.read_csv(old_csv_files[0])
        print(f"저번 달 총 인원 수 : {len(df_old)}, 저번 달 퇴사자: {len(df_old.loc[df_old['new']=="Out"])}")
        df_old = df_old.loc[df_old['new'] != "Out"]
        print(len(df_old), "명과 비교하여 퇴사자가 있는지 확인하겠습니다.")
        old_exist_data = set(df_old['url'].astype(str))
    else:
        print("참고할 이전 파일이 존재하지 않습니다.")
        df_old = pd.DataFrame()
        old_exist_data = set()
except FileNotFoundError:
    print("파일 탐색 과정에서 오류가 발생했습니다. 참고할 이전 파일 없이 크롤링을 진행합니다.")
    df_old = pd.DataFrame()
    old_exist_data = set()

# 데이터 프레임 정의
col = ['company','name','job','call','email','introduction','related_fields','career','education','eligibility','awards','assessment','performance','language','activity','url','new']
df = pd.DataFrame(columns=col)
# 회사명, 이름, 직업, 전화번호, 이메일, 상세 소개글, 업무분야, 경력, 학력, 자격, 수상, 외부평가(세종에만 있음), 주요업무실적, 사용언어, 외부활동, 프로필 url, 신규 여부

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
for category in tqdm.tqdm(range(2, len(categories)+1)):
    pf_data = []
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
                driver.execute_script("arguments[0].click();", pf)
                time.sleep(3)
                # 이메일
                email = driver.find_element(By.XPATH, '//*[@id="printDiv"]/div/div/div[1]/div[1]/div[2]/p[1]/a').text
                # 상세 소개글
                introduction = driver.find_element(By.CSS_SELECTOR, '.leeko-member-detail__text').text.replace('\n', ' ').strip()

                # 관련 분야
                fields_lst = driver.find_elements(By.CSS_SELECTOR, '.leeko-tag.leeko-tag--dark a')
                fields_total = []
                for field in fields_lst:
                    fields_total.append(field.text)
                related_fields = ','.join(fields_total)

                # 경력, 학력, 자격, 수상, 언어
                detail_table = driver.find_elements(By.CSS_SELECTOR, '.leeko-member-detail__table')
                eligibility, awards = "", ""
                for detail in detail_table:
                    detail_title = detail.find_element(By.XPATH, './/div[1]').text

                    if detail_title in ["경력", "학력", "자격/회원", "수상실적"]:
                        detail_contents = detail.find_elements(By.XPATH, './/div[2]//tr')
                        box_total = []
                        for detail_content in detail_contents:
                            period = detail_content.find_element(By.XPATH, './/th').get_attribute("textContent")
                            content = detail_content.find_element(By.XPATH, './/td').get_attribute("textContent")
                            box_total.append(f'{content} ({period})')

                        if detail_title == "경력":
                            career = ','.join(box_total)
                        elif detail_title == "학력":
                            education = ','.join(box_total)
                        elif detail_title == "자격/회원":
                            eligibility = ','.join(box_total)
                        else:
                            awards = ','.join(box_total)
                    elif detail_title == "언어":
                        language = detail.find_element(By.CSS_SELECTOR, ' td').text

                # 주요업무실적, 외부활동
                detail_table = driver.find_elements(By.CSS_SELECTOR, '.leeko-member-detail__list')
                performace, activity = "", ""
                for detail in detail_table:
                    detail_title = detail.find_element(By.XPATH, './/div[1]').text

                    if detail_title in ["주요처리사례", "저서/활동/기타"]:
                        dl_element = detail.find_element(By.CSS_SELECTOR, 'dl.leeko-more-contents')
                        children = dl_element.find_elements(By.XPATH, "./*")
                        detail_results = ""
                        for child in children:
                            child_text = child.get_attribute("textContent")
                            if child.tag_name == "dt":
                                if detail_results:
                                    detail_results += f'//{child_text.replace("[","").replace("]","")}]]'
                                else:
                                    detail_results += f'{child_text.replace("[","").replace("]","")}]]'
                            elif child.tag_name == "dd":
                                if detail_results:
                                    detail_results += f",{child_text}"
                                else:
                                    detail_results += child_text
                        if detail_title == "주요처리사례":
                            performance = detail_results
                        else:
                            activity = detail_results

                save_url = driver.current_url
                if old_exist_data:
                    if save_url in old_exist_data:
                        new = "-"
                    else:
                        new = "Y"
                else:
                    new = '-'

                add_pf = {
                            'company':company,
                            'name':name,
                            'job':job,
                            'call':call,
                            'email':email,
                            'introduction':introduction,
                            'related_fields':related_fields,
                            'career':career,
                            'education':education,
                            'eligibility':eligibility,
                            'awards':awards,
                            'assessment':"",
                            'performance':performance,
                            'language':language,
                            'activity':activity,
                            'url':save_url,
                            'new':new
                        }
                pf_data.append(add_pf)
                driver.back()
                time.sleep(3)
                
    # 카테고리 하나당 한번씩 df 갱신
    df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)

# 퇴사자 확인
if not df_old.empty:
    df_old['temp_id'] = df_old['url'].astype(str)
    df['temp_id'] = df['url'].astype(str)
    # 퇴사자 정보 추출
    retired_info = df_old[~df_old['temp_id'].isin(df['temp_id'])].copy()
    df.drop(columns=['temp_id'], inplace=True)

    if not retired_info.empty:
        retired_info['new'] = "Out"
        retired_info.drop(columns=['temp_id'], inplace=True)
        df = pd.concat([df, retired_info], ignore_index=True)

today_folder = datetime.now().strftime("%Y-%m-%d")
os.makedirs(f"data/{today_folder}", exist_ok=True)

today = datetime.now().strftime("%y%m%d")
df.to_csv(f"data/{today_folder}/Lee_Ko_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()