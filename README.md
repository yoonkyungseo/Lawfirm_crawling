# 국내 로펌 인사정보 크롤링 (Lawfirm Crawling)

## 📋 프로젝트 개요
국내 주요 로펌의 변호사 및 법무사 인사정보를 자동으로 크롤링하여 수집하는 프로젝트입니다.
Selenium을 활용한 동적 웹페이지 크롤링을 통해 체계적으로 인사정보 데이터를 수집합니다.

---

## 🎯 대상 로펌
- **김앤장 법률사무소** (Kim_and_Chang.py)
- **법무법인 태평양** (BKL.py)
- **법무법인 세종** (Shin_Kim.py)
- **법무법인 광장** (Lee_Ko.py)
- **법무법인 화우** (Hwawoo.py)

---

## 📁 프로젝트 구조

```
Lawfirm_crawling/
├── Kim_and_Chang.py               # 김앤장 크롤링
├── BKL.py                         # 태평양 크롤링
├── Shin_Kim.py                    # 세종 크롤링
├── Lee_Ko.py                      # 광장 크롤링
├── Hwawoo.py                      # 화우 크롤링
├── data/                          # 크롤링된 데이터 저장 폴더
├── .github/
│ └── workflows/
│ └────monthly_lawfirm_crawl.yml   # GitHub Actions 자동화 설정
├── requirements.txt               # 프로젝트 의존성
└── README.md                      # 프로젝트 문서
```

---

## 📊 수집 데이터 항목

각 스크립트에서 수집하는 인사정보:

| 항목 | 설명 |
|------|------|
| company | 로펌명 |
| name | PF 이름 |
| job | 직업/직책 |
| call | 연락처 |
| related_fields | 업무분야 |
| career | 경력 |
| education | 학력 |
| eligibility | 자격 |
| awards | 수상 |
| assessment | 외부평가 |

---

## 🛠 기술 스택

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| Selenium | - | 동적 웹페이지 크롤링 |
| Pandas | - | 데이터 처리 및 저장 |
| tqdm | - | 진행상황 표시 |
| webdriver-manager | - | ChromeDriver 자동 관리 |

---

## 📋 설치 및 실행

### 1️⃣ 필수 환경
- Python 3.7 이상
- Chrome 브라우저 설치

### 2️⃣ 의존성 설치
```bash
pip install -r requirements.txt
```

## 3️⃣ 로펌 크롤링 실행

#### ⏰ 실행 일정

```yaml
- cron: '0 0 1 * *'  # 매월 1일 자정 (UTC) = 한국 시간 오전 9시
```

#### 🔄 실행 방식

**🔹 자동 스케줄 실행**
- 매월 1일 오전 9시 (한국 시간)에 자동 실행

**🔹 수동 실행**
- GitHub 저장소 → `Actions` 탭 → `Monthly Law Firm Crawling` 선택
- 우측 `Run workflow` 버튼 클릭하여 즉시 실행 가능

#### 🔄 자동 커밋 정보

```
커밋 작성자: github-actions[bot]
커밋 메시지 형식: "Auto-update: Data for YYYY-MM-DD"
```

#### 📊 실행 결과

- 크롤링된 데이터는 `data/` 폴더에 저장
- 매번 실행 후 자동으로 저장소에 커밋 및 푸시
- GitHub Actions 로그에서 상세 실행 기록 확인 가능

---
## ⚙️ 크롤링 옵션

- `--headless` : 브라우저 창을 띄우지 않음 (백그라운드 실행)
- `--no-sandbox` : 보안 기능 해제 (리눅스 서버 완벽 지원)
- `--disable-dev-shm-usage` : 공유 메모리 부족 방지
- `--disable-gpu` : GPU 가속 해제
- `--window-size=1920,1080` : 가상 모니터 크기 설정 (렌더링 오류 방지)

---

## 🔍 주요 기능

✅ 중복 데이터 자동 처리  
✅ 가비지 컬렉션을 통한 메모리 효율화  
✅ 진행상황 실시간 표시 (tqdm)  
✅ 에러 처리 및 타임아웃 관리  
✅ 웹드라이버 자동 관리  
