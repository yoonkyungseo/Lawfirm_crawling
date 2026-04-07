import os
import gc
import time
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import tqdm
from selenium import webdriver
from selenium.webdriver.common. by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib3.exceptions import ReadTimeoutError
from datetime import datetime
import glob

# --- Github 환경 추가 라이브러리 ---
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

base_path = 'data'
try:
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    folders.sort()
    latest_folder = folders[-1] # 가장 최근 폴더 선택
    old_csv_files = glob.glob(os.path.join(f'data/{latest_folder}', "BKL*.csv"))
    if old_csv_files:
        df_old = pd.read_csv(old_csv_files[0])
        old_exist_data = set(zip(df_old['name'].fillna(''), df_old['email'].fillna('')))
    else:
        df_old = pd.DataFrame()
        old_exist_data = set()
except FileNotFoundError:
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

def create_driver():
    gc.collect()
    options = Options()
    options.add_argument("--headless")           # 브라우저 창을 띄우지 않음 (필수)
    options.add_argument("--no-sandbox")          # 보안 기능 해제 (리눅스 서버 필수)
    options.add_argument("--disable-dev-shm-usage") # 공유 메모리 부족 방지
    options.add_argument("--disable-gpu")         # GPU 가속 해제
    options.add_argument("--window-size=1920,1080") # 가상 모니터 크기 설정 (스크롤/클릭 오류 방지)
        
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# 태평양 크롤링 코드

# 주요 구성원 id = isMainY, button_id = 2
# 관련 구성원 id = isMainN, button_id = 3
# button_id는 "더보기 버튼" 클릭 시 XPATH 내 달라지는 div 리스트 넘버
def bkl_crawling(id, button_id):
    global df
    company = "태평양"
    page = 1

    driver = create_driver()
    driver.get("https://www.bkl.co.kr/law/member/allList.do?isMain=&pageIndex=1&searchCondition=&url=all&job=&lang=ko&memberNo=&searchYn=Y&logFunction=goSearch&searchKeyword=")
    driver.maximize_window()
    time.sleep(1)

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
            # 자격, 수상, 주요업무실적, 외부활동 없는 경우를 대비하여 기본값 설정
            eligibility, awards, performance, activity = "", "", "", ""
            
            # 해당 pf가 기존에 저장된 사람인지 확인
            if check_duplicates(name, job, call):
                pf.click()
                time.sleep(3)
                # 이메일
                email = driver.find_element(By.XPATH, '//*[@id="content"]/div[1]/div[1]/div[3]/ul[2]/li[3]/span[2]').text

                # 상세 소개글
                pf_introduction = driver.find_elements(By.XPATH, '//*[@id="content"]/div[3]/div[1]/div[1]/div[2]/p')
                intro_total = []
                for intro in pf_introduction:
                    intro_total.append(intro.text)
                introduction = ','.join(intro_total)

                # 관련 분야
                fields_lst = driver.find_elements(By.CSS_SELECTOR, ' div.prof-business-container ul.prof-business-list > li')
                fields_total = []
                for field in fields_lst:
                    field_text = field.find_element(By.XPATH, './/a').get_attribute("textContent")
                    fields_total.append(field_text)
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
                            # 기타 경력이 있다면 추가로 저장
                            try:
                                hidden_career = section.find_elements(By.CSS_SELECTOR, 'div.prof-list-container > div.prof-contents-hidden div')
                                for hidden in hidden_career:
                                    hidden_content = hidden.find_element(By.XPATH, './/span[2]').get_attribute("textContent")
                                    hidden_period = hidden.find_element(By.XPATH, './/span[1]').get_attribute("textContent")
                                    box_total.append(f'{hidden_content} ({hidden_period})')
                            except:
                                pass
                            career = ','.join(box_total)
                        elif title == "학력":
                            education = ','.join(box_total)
                        else:
                            eligibility = ','.join(box_total)
                    elif "주요활동" in title:
                        main_action_button = title_.find_element(By.XPATH, './/button')
                        driver.execute_script("arguments[0].click();", main_action_button)
                        time.sleep(0.3)
                        # 수상, 외부 활동
                        try:
                            contents_total = []
                            find_contents = section.find_elements(By.CSS_SELECTOR, " div.prof-list-container")
                            for what_contents in find_contents:
                                len_contents = what_contents.find_elements(By.XPATH, './/div')
                                contents_title = len_contents[0].text.strip()
                                contents_imsi = []
                                for cont in len_contents[1:]:
                                    contents_imsi.append(cont.text)
                                contents_text = ','.join(contents_imsi)
                                # 수상
                                if contents_title == "수상":
                                    awards = contents_text
                                # 외부활동
                                else:
                                    contents_total.append(f"{contents_title}]]{contents_text}")
                            activity = '//'.join(contents_total)
                        except:
                            pass
                    
                    # 주요 업무 실적
                    elif "주요 업무사례" in title:
                        performance_lst = section.find_elements(By.CSS_SELECTOR, 'div.prof-contents-full > div.prof-list-container')
                        performance_total = []
                        for perform in performance_lst:
                            # 주요 업무 사례에 세부제목이 있는 경우
                            try:
                                perform_title = perform.find_element(By.CSS_SELECTOR, 'div.prof-list-tit01').get_attribute("textContent")
                            except:
                                perform_title = ""
                            perform_contents = perform.find_elements(By.CSS_SELECTOR, 'div.prof-list-txt01')
                            perform_content_imsi = []
                            for perf_con in perform_contents:
                                perform_content_imsi.append(perf_con.get_attribute("textContent"))
                            perform_content_text = ','.join(perform_content_imsi)

                            if perform_title:
                                performance_total.append(f'{perform_title}]]{perform_content_text}')
                            else:
                                performance_total.append(perform_content_text)
                        performance = '//'.join(performance_total)

                if old_exist_data:
                    if (name, email) in old_exist_data:
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
                            'language':"", # 태평양은 사용언어 정보가 없음
                            'activity':activity,
                            'url':driver.current_url,
                            'new':new
                        }
                pf_data.append(add_pf)
                driver.back()
                time.sleep(4)
        # 더보기 버튼 클릭 전마다 df 갱신
        df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)
        current_url = driver.current_url

        try:
            # button = driver.find_element(By.XPATH, f'//*[@id="{id}"]/div[{button_id}]/button')
            button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="{id}"]/div[{button_id}]/button')))
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", button)
            button.click()
            time.sleep(2)
            current_url = driver.current_url
            driver.refresh()
            time.sleep(4)
            print(page, "페이지 완료")
            page += 1
        except ReadTimeoutError:
            driver.get(current_url)
            time.sleep(4)
        except:
            try:
                button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="{id}"]/div[{button_id}]/button')))
                driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", button)
                button.click()
                time.sleep(2)
                current_url = driver.current_url
                driver.refresh()
                time.sleep(4)
                print(page, "페이지 완료")
                page += 1
            except ReadTimeoutError:
                print("새로고침 오류로 브라우저를 완전히 닫고 새로 시작합니다.")
                driver.quit()
                time.sleep(2)
                driver = create_driver()
                driver.get(current_url)
                button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="{id}"]/div[{button_id}]/button'))) # 더보기 버튼 나타날때까지 url이 로딩되도록 대기
                print("재접속 완료")
            except TimeoutException:
                print(f"현재 {page} 페이지까지 완료")
                print("더보기 버튼을 찾을 수 없습니다.")
                break
            except Exception as e:
                print(f"페이지를 다시 불러오는 중 오류 발생: {e}")
    driver.quit()

bkl_crawling("isMainY", 2)
time.sleep(2)
print('-'*30)
bkl_crawling("isMainN", 3)

# 퇴사자 확인
if not df_old.empty:
    df_old['temp_id'] = df_old['name'].astype(str) + df_old['email'].astype(str)
    df['temp_id'] = df['name'].astype(str) + df['email'].astype(str)
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
df.to_csv(f"data/{today_folder}/BKL_{today}.csv", index=False, encoding='utf-8-sig')