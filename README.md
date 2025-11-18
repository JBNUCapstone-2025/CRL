# CRL - Emotion-based Book Crawler

**CRL (Crawling for Recommendation with LLM)** - 감정 기반 책 추천 시스템 데이터 수집 모듈

교보문고에서 감정별 책 데이터를 수집하여 RAG 기반 추천 시스템 구축을 위한 크롤러입니다.

---

## 📌 주요 기능

### 1. 감정별 책 크롤링
- 6가지 감정(기쁨, 설렘, 보통, 슬픔, 불안, 분노)에 따른 키워드 검색
- 각 감정당 5개 키워드 × 2개 정렬(인기순, 판매량순) × 3페이지
- ISBN 기준 자동 중복 제거

### 2. 풍부한 데이터 수집
- **기본 정보**: 제목, 저자, 출판사, 출판일, ISBN, 상품ID
- **추가 정보**: 부제목, 정가, 태그 배열
- **상세 링크**: 교보문고 상세 페이지 URL

### 3. 감정별 JSON 저장
- 감정별로 개별 JSON 파일 생성 (joy.json, sadness.json, ...)
- UTF-8 인코딩으로 한글 완벽 지원
- 할루시네이션 방지를 위한 원본 데이터 보존

### 4. 유연한 크롤링 제어
- 전체 감정 크롤링 (`--full`)
- 특정 감정만 선택 크롤링 (예: `joy sadness`)
- 요청 간 2초 딜레이로 서버 부담 최소화

---

## 🛠 기술 스택

| Category | Technology |
|----------|-----------|
| **언어** | Python 3.8+ |
| **HTTP 요청** | requests |
| **HTML 파싱** | BeautifulSoup4 |
| **데이터 저장** | JSON (UTF-8) |

---

## 🏗 프로젝트 구조

```
CRL/
├── crawl_books.py              # 메인 크롤러 스크립트
├── requirements.txt            # 패키지 의존성
├── README.md                   # 프로젝트 문서 (이 파일)
├── .gitignore                  # Git 제외 목록
└── data/                       # 크롤링 결과 저장 (git 제외)
    └── books/                  # 책 데이터 JSON 파일
        ├── joy.json            # 기쁨 (275개)
        ├── excitement.json     # 설렘 (299개)
        ├── normal.json         # 보통 (299개)
        ├── sadness.json        # 슬픔 (295개)
        ├── anxiety.json        # 불안 (299개)
        └── anger.json          # 분노 (289개)
```

### 코드 구조 (crawl_books.py)

```
crawl_books.py
├── Configuration               # 설정
│   ├── EMOTION_KEYWORDS        # 감정별 검색 키워드
│   ├── PAGES_PER_KEYWORD       # 키워드당 페이지 수 (3)
│   ├── SORT_TYPES              # 정렬 방식 (best, sale)
│   └── DELAY_SECONDS           # 요청 간 딜레이 (2초)
│
├── Parsing Functions           # 파싱
│   └── parse_book_item()       # 책 정보 파싱 (10가지 항목)
│
├── Crawling Functions          # 크롤링
│   └── crawl_keyword()         # 키워드 1개 크롤링
│
├── Data Management             # 데이터 관리
│   ├── remove_duplicates()     # ISBN 기준 중복 제거
│   └── save_to_json()          # 감정별 JSON 저장
│
├── Orchestration               # 오케스트레이션
│   ├── crawl_emotion()         # 한 감정 크롤링
│   └── crawl_all_emotions()    # 전체 감정 크롤링
│
└── Main Execution              # 실행
    └── main()                  # CLI 인자 처리
```

---

## ⚙️ 설치 및 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 크롤링 실행

#### 사용법 확인
```bash
python crawl_books.py
```

#### 특정 감정 1개 크롤링
```bash
python crawl_books.py joy
```

#### 특정 감정 여러 개 크롤링
```bash
python crawl_books.py sadness anxiety anger
```

#### 전체 6개 감정 크롤링
```bash
python crawl_books.py --full
```

**결과 확인:**
- 크롤링 결과는 `data/` 디렉토리에 JSON 파일로 저장됩니다.
- 각 파일은 감정별로 중복 제거된 고유한 책 목록을 포함합니다.

---

## 📊 크롤링 통계 (2025-11-18 최종)

### 감정별 수집량
- **각 감정당**: 5개 키워드 × 2개 정렬(best, sale) × 3페이지 × 최대 20개/페이지 = 최대 600개
- **중복 제거 후 실제 수집량**:
  - joy (기쁨): **275개**
  - excitement (설렘): **299개**
  - normal (보통): **299개**
  - sadness (슬픔): **295개**
  - anxiety (불안): **299개**
  - anger (분노): **289개**
  - **총합: 1,756개 고유 책** (부제목, 정가, 태그 포함)

### 소요 시간
- 1개 감정: 약 1~2분 (30번 요청 × 2초 딜레이)
- 전체 6개 감정: 약 6~8분

### 데이터 크기
- 각 JSON 파일: 약 135~147KB (275~299개 책)
- 전체 6개 JSON: 약 857KB (1,756개 책)

---

## 📝 데이터 구조

### JSON 형식 (data/*.json)

```json
[
  {
    "product_id": "S000001829833",
    "isbn": "9791164451920",
    "title": "거울나라의 앨리스(초판본)(1871년 오리지널 초판본 패브릭 양장 에디션)",
    "author": "루이스 캐럴",
    "publisher": "더스토리",
    "pub_date": "2020년 03월 10일",
    "subtitle": "양장본 HardCover",
    "price": "12,000원",
    "tags": [
      "세계고전문학",
      "영국고전",
      "영국소설",
      "판타지소설",
      "환상문학",
      "상상",
      "여행",
      "모험",
      "유머",
      "풍자"
    ],
    "detail_url": "https://product.kyobobook.co.kr/detail/S000001829833"
  }
]
```

---

## 🎯 감정별 검색 키워드

| 감정 | 검색 키워드 |
|------|------------|
| **기쁨 (joy)** | 유머, 재미있는 소설, 힐링, 따뜻한 에세이, 동기부여 |
| **설렘 (excitement)** | 새로운 시작, 여행 에세이, 영감, 도전, 로맨스 소설 |
| **보통 (normal)** | 에세이, 일상, 취미, 요리, 소설 베스트셀러 |
| **슬픔 (sadness)** | 위로, 공감, 치유, 성장 소설, 괜찮아 |
| **불안 (anxiety)** | 용기, 자존감, 극복, 심리, 안정 |
| **분노 (anger)** | 마음챙김, 명상, 평온, 스트레스 해소, 감정 조절 |

---

## 💡 사용 예시

### 예시 1: 슬픔 감정 크롤링
```bash
python crawl_books.py sadness
```

**출력:**
```
============================================================
Crawling emotion: sadness
Keywords: ['위로', '공감', '치유', '성장 소설', '괜찮아']
============================================================

[Keyword] 위로
  [Sort] best
Crawling: https://search.kyobobook.co.kr/search?keyword=위로&target=kyobo&sort=best&page=1
[OK] Page loaded: 156234 bytes
[OK] Found 20 book items
[OK] Successfully parsed 20 books
...

[Summary] Total books before deduplication: 314
[Summary] Unique books after deduplication: 295
[OK] Saved 295 books to data/sadness.json

[DONE] sadness: 295 books saved
```

### 예시 2: 전체 감정 크롤링
```bash
python crawl_books.py --full
```

**결과:**
- `data/joy.json` (275개)
- `data/excitement.json` (299개)
- `data/normal.json` (299개)
- `data/sadness.json` (295개)
- `data/anxiety.json` (299개)
- `data/anger.json` (289개)

---

## 🚀 다음 단계: RAG 시스템 구축 (예정)

### Phase 2 목표
크롤링된 데이터를 활용하여 감정 기반 책 추천 시스템 개발

### 구축 예정 항목
1. **JSON 데이터 로딩** - LangChain JSON Loader
2. **텍스트 청크 분해** - 제목, 부제목, 태그 조합
3. **임베딩 생성** - OpenAI/HuggingFace 임베딩
4. **벡터 DB 저장** - FAISS/Chroma/Pinecone
5. **LLM 연동** - 감정 분석 + 책 추천

---

## 🔒 주의사항

### 법적 준수
- ✅ 교보문고 robots.txt 및 이용약관 준수
- ✅ 크롤링 시 서버 부담 최소화 (요청 간 2초 딜레이)
- ✅ 개인적/교육적 목적으로만 사용

### 기술적 고려사항
- ✅ 에러 처리 구현 (timeout 10초)
- ✅ ISBN 기준 중복 제거로 데이터 정확성 확보
- ⚠️ Windows CMD에서 한글 깨짐 (JSON 파일은 UTF-8로 정상)

---

## 🔗 관련 링크

- [BeautifulSoup 공식 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests 공식 문서](https://requests.readthedocs.io/)
- [교보문고](https://www.kyobobook.co.kr/)

---

## 📄 License

This project is for educational purposes (Capstone Project).

---

## 👥 Team

**캡스톤 프로젝트 - ICSYF Team**

*"I Can See Your Feelings - 감정 기반 정서 관리 플랫폼"*
