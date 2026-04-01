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
try:
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    folders.sort()
    latest_folder = folders[-1] # 가장 최근 폴더 선택
    old_csv_files = glob.glob(os.path.join(f'data/{latest_folder}', "Kim_and_Chang*.csv"))
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


# 김앤장 크롤링 코드

driver.get("https://www.kimchang.com/ko/professionals/index.kc")
main_window = driver.current_window_handle # 현재 창 ID를 변수로 저장
driver.maximize_window()
time.sleep(3)

all_button = wait_presence_element(driver, (By.XPATH, '//*[@id="form1"]/div[2]/ul/li[2]/a/span'))
driver.execute_script("arguments[0].click();", all_button)

company = "김앤장"
# 김앤장 구성원 페이지 산업별(Industry) 구분 클릭
elements = wait_presence_elements(driver, (By.XPATH, '//*[@id="keyWordTab2"]/li'))
for num in tqdm.tqdm(range(1, len(elements)+1)):
    practice = wait_presence_element(driver, (By.XPATH, f'//*[@id="keyWordTab2"]/li[{num}]/a')) # 구분 목록 요소
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", practice)
    # 현재 진행 중인 구분 목록 출력
    print("-----", practice.get_attribute("textContent").strip(), "-----")
    pf_data = []
    driver.execute_script("arguments[0].click();", practice) # 해당 구분 목록 클릭
    time.sleep(5) # 구분 목록 클릭 후 로딩 시간 부여

    # 페이지 갯수 확인
    current_page_idx = 1

    try_again = 0
    while True:
        # 페이지별 탐색
        print(f"현재 {current_page_idx} page 진행중")
        try:
            pf_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="_pro"]/ul[2]/li'))
            current_pf_num = len(pf_lst)

            # for j in range(1, len(pf_lst)+1):
            for j in range(3, len(pf_lst)+1):
                pf = wait_presence_element(driver, (By.CSS_SELECTOR, f'#_pro > ul.lawyer_profile > li:nth-child({j})'))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pf)
                # 이름 # 직업
                job = wait_presence_element(pf, (By.XPATH, './/div/span[1]/a/span')).get_attribute("textContent").strip()
                name = wait_presence_element(pf, (By.XPATH, './/div/span[1]/a')).get_attribute("textContent").replace(job, "").strip()
                # 전화번호
                call = wait_presence_element(pf, (By.XPATH, './/div/span[2]')).get_attribute("textContent").replace('T.','')
                print(name, job, call)
                    

                # 해당 pf가 기존에 저장된 사람인지 확인
                if check_duplicates(name, job, call):
                    # pf 화면 클릭
                    pf_link = wait_presence_element(pf, (By.CSS_SELECTOR, "img"))
                    driver.execute_script("arguments[0].click();", pf_link)
                    time.sleep(2)

                    # 이메일
                    email = wait_presence_element(driver, (By.XPATH, "//a[contains(@href, 'mailto:')]")).get_attribute("textContent")

                    # 상세 소개글
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
                    career_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/div[1]//*'))
                    career_total = []
                    for careers in career_lst:
                        career_total.append(careers.get_attribute("textContent").replace('\n', ' ').strip())
                    career = ','.join(career_total)

                    # 학력
                    edu_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/ul[1]//*'))
                    edu_total = []
                    for edus in edu_lst:
                        edu_total.append(edus.get_attribute("textContent").replace('\n', ' ').strip())
                    education = ','.join(edu_total)

                    # 자격
                    try:
                        eli_lst = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/ul[2]//*'))
                        eli_total = []
                        for elis in eli_lst:
                            eli_total.append(elis.get_attribute("textContent").replace('\n', ' ').strip())
                        eligibility = ','.join(eli_total)
                    except:
                        eligibility = ""

                    # 언어
                    try:
                        lan_lst = wait_presence_elements(driver, (By.CSS_SELECTOR, '#career > p.lang'))
                        lan_total = []
                        for lan in lan_lst:
                            lan_total.append(lan.get_attribute("textContent").replace('\n', ' ').strip())
                        language = ','.join(lan_total)
                    except:
                        language = ""
                    
                    # 수상, 외부 활동, 주요 업무 실적
                    awards, activity, performance = "", "", ""
                    try:
                        extra_bullet = wait_presence_elements(driver, (By.XPATH, '//*[@id="career"]/div[2]/div'))
                    except:
                        extra_bullet = []
                    for extra in extra_bullet:
                        main_activity = wait_presence_element(extra, (By.XPATH, './/h4/a'))
                        # 수상, 외부 활동
                        if "주요 활동" in main_activity.get_attribute("textContent"):
                            print("주요 활동")
                            driver.execute_script("arguments[0].click();", main_activity)
                            main_activity_bullet = wait_presence_elements(extra, (By.XPATH, './/div/h5'))
                            for act in main_activity_bullet:
                                if act.get_attribute("textContent") == "수상":
                                    print("수상")
                                    awards_lst = wait_presence_elements(extra, (By.XPATH, './/div/ul[1]/li'))
                                    award_total = []
                                    for award in awards_lst:
                                        award_total.append(award.get_attribute("textContent"))
                                    awards = ','.join(award_total)
                                elif act.get_attribute("textContent") == "저서 및 외부활동":
                                    print("외부 활동")
                                    activity_lst = wait_presence_elements(extra, (By.CSS_SELECTOR, ' ul.field_history *'))
                                    imsi_tit = []
                                    imsi_cont = ""
                                    imsi_cont_lst = []
                                    for plus_act in activity_lst:
                                        if plus_act.tag_name == "div":
                                            txt_tit = plus_act.get_attribute("textContent").replace("[","").replace("]","").strip()
                                            if txt_tit:
                                                imsi_tit.append(txt_tit)
                                            if imsi_cont:
                                                imsi_cont_lst.append(imsi_cont)
                                                imsi_cont = ""
                                        elif plus_act.tag_name == "li":
                                            if imsi_cont:
                                                imsi_cont += f',{plus_act.get_attribute("textContent").strip()}'
                                            else:
                                                imsi_cont = plus_act.get_attribute("textContent").strip()
                                    if imsi_tit and imsi_cont:
                                        imsi_cont_lst.append(imsi_cont)
                                    if imsi_tit:
                                        activity_total = []
                                        for t, c in zip(imsi_tit, imsi_cont_lst):
                                            activity_total.append(f'{t}]]{c}')
                                        activity = '//'.join(activity_total)
                                    else:
                                        activity = imsi_cont
                        # 주요 업무 실적
                        elif "주요 실적" in main_activity.get_attribute("textContent"):
                            print("주요 실적")
                            perf_lst = wait_presence_elements(extra, (By.XPATH, './/div[@class="box_open"]//*'))
                            print(len(perf_lst))
                            imsi_tit = []
                            imsi_cont = ""
                            imsi_cont_lst = []
                            for perf in perf_lst:
                                print(perf.tag_name)
                                if perf.tag_name == 'strong':
                                    txt_tit = perf.get_attribute("textContent").replace("[","").replace("]","").strip()
                                    if txt_tit:
                                        imsi_tit.append(txt_tit)
                                    if imsi_cont:
                                        imsi_cont_lst.append(imsi_cont)
                                        imsi_cont = ""
                                elif perf.tag_name == "li":
                                    if imsi_cont:
                                        imsi_cont += f',{perf.get_attribute("textContent").strip()}'
                                        print("li + 추가")
                                    else:
                                        imsi_cont = perf.get_attribute("textContent").strip()
                                        print("li 첫 추가")
                            if imsi_tit and imsi_cont:
                                imsi_cont_lst.append(imsi_cont)
                            if imsi_tit:
                                perf_total = []
                                for t, c in zip(imsi_tit, imsi_cont_lst):
                                    perf_total.append(f'{t}]]{c}')
                                performance = '//'.join(perf_total)
                            else:
                                performance = imsi_cont

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
                    print(add_pf)
                    
                    pf_data.append(add_pf)
                    driver.back()
                    time.sleep(2)

            # 다음 페이지로 넘기기
            try:
                next_page_idx = current_page_idx + 1
                target_page_btn = wait_clickable_element(driver, (By.XPATH, f'//div[@class="paging"]//a[text()="{next_page_idx}"]'))
                driver.execute_script("arguments[0].click();", target_page_btn)
                current_page_idx += 1
            except:
                try:
                    next_step_page_btn = wait_clickable_element(driver, (By.XPATH, '//div[@class="paging"]//a[@class="next hidden_text"]'))
                    driver.execute_script("arguments[0].click();", next_step_page_btn)
                    time.sleep(3)

                    next_page_idx = current_page_idx + 1
                    target_page_btn = wait_clickable_element(driver, (By.XPATH, f'//div[@class="paging"]//a[text()="{next_page_idx}"]'))
                    driver.execute_script("arguments[0].click();", target_page_btn)
                    current_page_idx += 1
                except:
                    print("마지막 페이지입니다.")
                    break
        except:
            if try_again <= 5:
                driver.refresh()
                try_again += 1
                time.sleep(2)
            else:
                print("페이지 로딩 문제로 중단")
                break

    # 구분목록 하나당 한번씩 df 갱신
    df = pd.concat([df, pd.DataFrame(pf_data)], ignore_index=True)

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
df.to_csv(f"data/{today_folder}/Kim_and_Chang_{today}.csv", index=False, encoding='utf-8-sig')

driver.quit()