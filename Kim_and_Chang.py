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
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
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
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36") # 최신 크롬 브라우저의 User-Agent로 설정 (봇 탐지 회피)

base_path = 'data'
folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
folders.sort()
latest_folder = folders[-1] # 가장 최근 폴더 선택
old_csv_files = glob.glob(os.path.join(f'data/{latest_folder}', "Kim_and_Chang*.csv"))
if old_csv_files:
    df_old = pd.read_csv(old_csv_files[0])
    old_exist_data = set(zip(df_old['name'].fillna(''), df_old['email'].fillna('')))
else:
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

def wait_presence_element(driver, locator, timeout=15):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
def wait_presence_elements(driver, locator, timeout=15):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located(locator))
def wait_visibility_element(driver, locator, timeout=15):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
def wait_clickable_element(driver, locator, timeout=15):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
def get_text_by_js(selector):
    return driver.execute_script(f"return document.querySelector('{selector}') ? document.querySelector('{selector}').textContent : '';").strip()
def grab_all_visible_text(driver):
    # 1. 페이지 로딩 및 동적 요소 생성을 위해 강제 대기
    # 김앤장 사이트는 스크롤이 트리거가 되므로 바닥까지 내렸다가 위로 올립니다.
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # 2. 자바스크립트로 화면에 보이는 모든 텍스트 추출
    # innerText는 불필요한 태그 정보를 제외한 '순수 글자'만 반환합니다.
    all_text = driver.execute_script("return document.body.innerText;")
    
    return all_text

# 김앤장 크롤링 코드

driver.get("https://www.kimchang.com/ko/professionals/index.kc")
main_window = driver.current_window_handle # 현재 창 ID를 변수로 저장
driver.maximize_window()
time.sleep(3)

all_button = wait_presence_element(driver, (By.XPATH, '//*[@id="form1"]/div[2]/ul/li[4]/a/span'))
driver.execute_script("arguments[0].click();", all_button)

company = "김앤장"
# 김앤장 구성원 페이지 ALL 항목들 = 구분 목록
elements = wait_presence_elements(driver, (By.XPATH, '//*[@id="keyWordTab4"]/li'))
# for num in tqdm.tqdm(range(1, len(elements)+1)):
for num in tqdm.tqdm(range(1, 2)):
    practice = wait_presence_element(driver, (By.XPATH, f'//*[@id="keyWordTab4"]/li[{num}]/a')) # 구분 목록 요소
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", practice)
    # 현재 진행 중인 구분 목록 출력
    print("-----", practice.get_attribute("textContent").strip(), "-----")
    pf_data = []
    driver.execute_script("arguments[0].click();", practice) # 해당 구분 목록 클릭

    # 페이지 갯수 확인
    pages = wait_presence_elements(driver, (By.XPATH, '//*[@id="_pro"]/div/a'))
    if len(pages) == 9:
        # 페이지가 5개 이상일 때
        start = 3
        end = len(pages)-1
        page_flag = True
    else:
        # 페이지가 5개 이하일 때
        start = 2
        end = len(pages)
        page_flag = False
    
    pf_flag = True
    while pf_flag:
        # 페이지별 탐색
        for i in range(start, end):
            # 페이지 이동
            page = wait_clickable_element(driver, (By.XPATH, f'//*[@id="_pro"]/div/a[{i}]'))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page)
            page_num = page.get_attribute("textContent")
            print(f"현재 {page_num} page 진행중")
            driver.execute_script("arguments[0].click();", page)
            time.sleep(3)

            pf_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="_pro"]/ul[2]/li'))
            for j in range(1, len(pf_lst)+1):
                pf = wait_presence_element(driver, (By.CSS_SELECTOR, f'#_pro > ul.lawyer_profile > li:nth-child({j})'))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pf)
                # 이름 # 직업
                name, job = wait_presence_element(pf, (By.XPATH, './/div/span[1]/a')).get_attribute("textContent").split()
                # 전화번호
                call = wait_presence_element(pf, (By.XPATH, './/div/span[2]')).get_attribute("textContent").replace('T.','')
                print(name, job, call)
                

                # 해당 pf가 기존에 저장된 사람인지 확인
                if check_duplicates(name, job, call):
                    # pf 화면 새 창에서 열기
                    pf_link = wait_presence_element(pf, (By.CSS_SELECTOR, "img"))
                    driver.execute_script("arguments[0].click();", pf_link)
                    time.sleep(5)

                    # all_content = grab_all_visible_text(driver)
                    # print(f"추출 결과: {all_content}")

                    # 이메일
                    email = wait_presence_element(driver, (By.XPATH, "//a[contains(@href, 'mailto:')]")).get_attribute("textContent")

                    # 상세 소개글
                    # introduction = wait_presence_element(driver, (By.CSS_SELECTOR, ".top_text.hidden_area")).get_attribute("textContent").replace('\n', ' ').strip()
                    introduction = ""
                    try:
                        introductions = wait_presence_elements(driver, (By.CSS_SELECTOR, '.top_text.hidden_area p'))
                        for intro in introductions:
                            introduction += intro.get_attribute("textContent").replace('\n', ' ').strip()
                    except:
                        pass

                    # 관련 분야
                    fields_lst = wait_presence_elements(driver, (By.CSS_SELECTOR, 'div.left_tag li'))
                    fields_total = []
                    for field in fields_lst:
                        fields_total.append(field.get_attribute("textContent").replace('\n', ' ').strip())
                    related_fields = ','.join(fields_total)

                    # 경력
                    career_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/div[1]/p'))
                    career_total = []
                    for careers in career_lst:
                        career_total.append(careers.get_attribute("textContent"))
                    career = ','.join(career_total)

                    # 학력
                    edu_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/ul[1]/p'))
                    edu_total = []
                    for edus in edu_lst:
                        edu_total.append(edus.get_attribute("textContent"))
                    education = ','.join(edu_total)

                    # 자격
                    eli_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/ul[2]/p'))
                    eli_total = []
                    for elis in eli_lst:
                        eli_total.append(elis.get_attribute("textContent"))
                    eligibility = ','.join(eli_total)

                    # 언어
                    lan_lst = wait_presence_elements(driver, (By.CSS_SELECTOR, '#career > p.lang'))
                    lan_total = []
                    for lan in lan_lst:
                        lan_total.append(lan.get_attribute("textContent").replace('\n', ' ').strip())
                    language = ','.join(lan_total)
                    
                    # 수상, 외부 활동, 주요 업무 실적
                    awards, activity, performance = "", "", ""
                    try:
                        extra_bullet = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/div[2]/div'))
                    except:
                        extra_bullet = []
                    for extra in extra_bullet:
                        main_activity = wait_presence_element(extra, (By.XPATH, './/h4/a'))
                        # 수상, 외부 활동
                        if main_activity.get_attribute("textContent") == "주요 활동":
                            driver.execute_script("arguments[0].click();", main_activity)
                            main_activity_bullet = wait_presence_elements(extra, (By.XPATH, './/div/h5'))
                            for act in main_activity_bullet:
                                if act.get_attribute("textContent") == "수상":
                                    awards_lst = wait_presence_elements(extra, (By.XPATH, './/div/ul[1]/li'))
                                    award_total = []
                                    for award in awards_lst:
                                        award_total.append(award.get_attribute("textContent"))
                                    awards = ','.join(award_total)
                                elif act.get_attribute("textContent") == "저서 및 외부활동":
                                    activity_lst = wait_presence_elements(extra, (By.CSS_SELECTOR, ' ul.field_history li'))
                                    activity_total = []
                                    for plus_act in activity_lst:
                                        activity_total.append(plus_act.get_attribute("textContent"))
                                    activity = ','.join(activity_total)
                        # 주요 업무 실적
                        elif main_activity.get_attribute("textContent") == "주요 실적":
                            perf_lst = wait_presence_elements(extra, (By.CSS_SELECTOR, 'div.boxopen li'))
                            perf_total = []
                            for perf in perf_lst:
                                perf_total.append(perf.get_attribute("textContent"))
                            performance = ','.join(perf_total)

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
                        'language':language,
                        'activity':activity,
                        'url':driver.current_url,
                        'new':new
                    }
                    ## 디버깅용
                    print(add_pf)
                    pf_data.append(add_pf)
                    driver.back()
                    time.sleep(5)

            if len(pf_lst) < 10:
                pf_flag = False
                break
        # 다음 페이지로 넘기기
        if page_flag and pf_flag:
            next_page = wait_clickable_element(driver, (By.XPATH, f'//*[@id="_pro"]/div/a[{end}]'))
            driver.execute_script("arguments[0].click();", next_page)
            start_page = wait_visibility_element(driver, (By.XPATH, f'//*[@id="_pro"]/div/a[{start}]')).get_attribute("textContent")
            if int(start_page) == int(page_num)+1:
                pages = wait_presence_elements(driver, (By.XPATH, '//*[@id="_pro"]/div/a'))
                start = 3
                end = len(pages)-1
            else:
                pf_flag = False
                
    # 구분목록 하나당 한번씩 df 갱신
    df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)

    time.sleep(2)

# 퇴사자 확인
if df_old:
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
df.to_csv(f"data/{today_folder}/Kim_and_Chang_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()