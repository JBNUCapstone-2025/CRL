# CRL - Emotion-based Content Crawler

**CRL (Crawling for Recommendation with LLM)** - 감정 기반 컨텐츠 추천 시스템 데이터 수집 모듈

교보문고에서 감정별 **책** 데이터를, 멜론에서 감정별 **음악** 데이터를 수집하여 RAG 기반 추천 시스템 구축을 위한 크롤러입니다.

---

## 📌 주요 기능

### 1. 감정별 책 크롤링 (교보문고)
- 6가지 감정(기쁨, 설렘, 보통, 슬픔, 불안, 분노)에 따른 키워드 검색
- 각 감정당 5개 키워드 × 2개 정렬(인기순, 판매량순) × 3페이지
- ISBN 기준 자동 중복 제거
- **수집 데이터**: 제목, 저자, 출판사, 출판일, ISBN, 부제목, 정가, 태그, 표지 이미지 URL
- **결과**: 총 1,755권 (6개 감정)

### 2. 감정별 음악 크롤링 (멜론)
- 6가지 감정에 따른 장르별 스테디셀러 곡 수집
- 각 감정당 2개 장르 × 최대 10페이지 (AJAX 페이징)
- Song ID 기준 자동 중복 제거
- **수집 데이터**: 곡 제목, 아티스트, 앨범, 장르, DJ 태그, 앨범 커버 URL (180px, quality 100)
- **결과**: joy 421곡 완료, 나머지 5개 감정 진행 예정

### 3. 감정별 JSON 저장
- 감정별로 개별 JSON 파일 생성
- UTF-8 인코딩으로 한글 완벽 지원
- 할루시네이션 방지를 위한 원본 데이터 보존

### 4. 유연한 크롤링 제어
- 전체 감정 크롤링 (`--full`)
- 특정 감정만 선택 크롤링 (예: `joy sadness`)
- 딜레이 설정으로 서버 부담 최소화

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
├── crawl_books.py              # 책 크롤러 스크립트
├── crawl_music.py              # 음악 크롤러 스크립트
├── requirements.txt            # 패키지 의존성
├── README.md                   # 프로젝트 문서 (이 파일)
├── CLAUDE.md                   # Claude Code 프로젝트 가이드
├── .gitignore                  # Git 제외 목록
└── data/                       # 크롤링 결과 저장 (git 제외)
    ├── books/                  # 책 데이터 JSON 파일 (완료 ✅)
    │   ├── joy.json            # 기쁨 (275권)
    │   ├── excitement.json     # 설렘 (298권)
    │   ├── normal.json         # 보통 (299권)
    │   ├── sadness.json        # 슬픔 (294권)
    │   ├── anxiety.json        # 불안 (299권)
    │   └── anger.json          # 분노 (290권)
    └── musics/                 # 음악 데이터 JSON 파일 (진행 중 🔄)
        ├── joy.json            # 기쁨 (421곡) ✅
        ├── excitement.json     # 설렘 ⏳
        ├── normal.json         # 보통 ⏳
        ├── sadness.json        # 슬픔 ⏳
        ├── anxiety.json        # 불안 ⏳
        └── anger.json          # 분노 ⏳
```

### 코드 구조

#### crawl_books.py (책 크롤러)
```
crawl_books.py
├── Configuration               # 설정
│   ├── EMOTION_KEYWORDS        # 감정별 검색 키워드
│   ├── PAGES_PER_KEYWORD       # 키워드당 페이지 수 (3)
│   ├── SORT_TYPES              # 정렬 방식 (best, sale)
│   └── DELAY_SECONDS           # 요청 간 딜레이 (2초)
│
├── Parsing Functions           # 파싱
│   └── parse_book_item()       # 책 정보 파싱 (11가지 항목)
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

#### crawl_music.py (음악 크롤러)
```
crawl_music.py
├── Configuration               # 설정
│   ├── EMOTION_GENRES          # 감정별 장르 매핑
│   ├── GENRE_CODES             # 장르 코드 목록
│   ├── MIN_DELAY / MAX_DELAY   # 랜덤 딜레이 (2~5초)
│   └── TIMEOUT                 # 타임아웃 (10초)
│
├── Parsing Functions           # 파싱
│   ├── parse_song_list()       # 목록 페이지 (6개 항목)
│   └── parse_song_detail()     # 상세 페이지 (2개 항목)
│
├── Crawling Functions          # 크롤링
│   ├── crawl_genre_list()      # 장르별 목록 (페이징)
│   └── crawl_song_detail()     # 상세 페이지
│
├── Data Management             # 데이터 관리
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

#### 책 크롤링 (교보문고)

**사용법 확인:**
```bash
python crawl_books.py
```

**특정 감정 크롤링:**
```bash
python crawl_books.py joy
python crawl_books.py sadness anxiety anger
```

**전체 감정 크롤링:**
```bash
python crawl_books.py --full
```

#### 음악 크롤링 (멜론)

**사용법 확인:**
```bash
python crawl_music.py
```

**특정 감정 크롤링:**
```bash
python crawl_music.py joy
python crawl_music.py excitement normal
```

**전체 감정 크롤링:**
```bash
python crawl_music.py --full
```

**결과 확인:**
- 크롤링 결과는 `data/books/` 및 `data/musics/` 디렉토리에 JSON 파일로 저장됩니다.
- 각 파일은 감정별로 중복 제거된 고유한 데이터를 포함합니다.

---

## 📊 크롤링 통계

### 책 데이터 (완료 ✅ 2025-11-19)
- **각 감정당**: 5개 키워드 × 2개 정렬(best, sale) × 3페이지 × 최대 20개/페이지 = 최대 600개
- **중복 제거 후 실제 수집량**:
  - joy (기쁨): **275권**
  - excitement (설렘): **298권**
  - normal (보통): **299권**
  - sadness (슬픔): **294권**
  - anxiety (불안): **299권**
  - anger (분노): **290권**
  - **총합: 1,755권** (부제목, 정가, 태그, 표지 이미지 URL 포함)
  - **필터링**: ISBN 없는 펀딩/이벤트 상품 자동 제외
- **소요 시간**: 전체 6개 감정 약 9~10분
- **데이터 크기**: 전체 약 1,030KB

### 음악 데이터 (진행 중 🔄 2025-11-21)
- **각 감정당**: 2개 장르 × 최대 10페이지 × 50곡 = 최대 1,000곡
- **중복 제거 후 실제 수집량**:
  - joy (기쁨): **421곡** ✅ (댄스 392 + POP 29)
  - excitement (설렘): ⏳ 진행 예정
  - normal (보통): ⏳ 진행 예정
  - sadness (슬픔): ⏳ 진행 예정
  - anxiety (불안): ⏳ 진행 예정
  - anger (분노): ⏳ 진행 예정
- **소요 시간**: 1개 감정 약 8~10분 (상세 페이지 크롤링 포함)
- **필터링**: (Inst.), (MR) 제목 자동 제외

---

## 📝 데이터 구조

### 책 데이터 (data/books/*.json)

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
    "detail_url": "https://product.kyobobook.co.kr/detail/S000001829833",
    "cover_image_url": "https://contents.kyobobook.co.kr/sih/fit-in/300x0/pdt/9791164451920.jpg"
  }
]
```

### 음악 데이터 (data/musics/*.json)

```json
[
  {
    "song_id": "1325050",
    "title": "롤러코스터",
    "artist": "소녀시대",
    "album": "소녀시대 첫!!",
    "cover_url": "https://cdnimg.melon.co.kr/cm/album/images/003/22/845/322845_500.jpg/melon/resize/180/quality/100/optimize",
    "detail_url": "https://www.melon.com/song/detail.htm?songId=1325050",
    "genre": "댄스",
    "dj_tags": ["#앨범", "#댄스", "#중독", "#2000년"]
  }
]
```

---

## 🎯 감정별 매핑

### 책 검색 키워드 (교보문고)

| 감정 | 검색 키워드 |
|------|------------|
| **기쁨 (joy)** | 유머, 재미있는 소설, 힐링, 따뜻한 에세이, 동기부여 |
| **설렘 (excitement)** | 새로운 시작, 여행 에세이, 영감, 도전, 로맨스 소설 |
| **보통 (normal)** | 에세이, 일상, 취미, 요리, 소설 베스트셀러 |
| **슬픔 (sadness)** | 위로, 공감, 치유, 성장 소설, 괜찮아 |
| **불안 (anxiety)** | 용기, 자존감, 극복, 심리, 안정 |
| **분노 (anger)** | 마음챙김, 명상, 평온, 스트레스 해소, 감정 조절 |

### 음악 장르 매핑 (멜론)

| 감정 | 장르 코드 | 장르명 |
|------|----------|--------|
| **기쁨 (joy)** | GN0200, GN0900 | 댄스, POP |
| **설렘 (excitement)** | GN0500, GN1500 | 인디음악, OST |
| **보통 (normal)** | GN0500, GN0800 | 인디음악, 포크/블루스 |
| **슬픔 (sadness)** | GN0400, GN0100 | R&B/Soul, 발라드 |
| **불안 (anxiety)** | GN0400, GN0800 | R&B/Soul, 포크/블루스 |
| **분노 (anger)** | GN0300, GN0600 | 랩/힙합, 록/메탈 |

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
- `data/excitement.json` (298개)
- `data/normal.json` (299개)
- `data/sadness.json` (294개)
- `data/anxiety.json` (299개)
- `data/anger.json` (290개)

---

## 🔒 주의사항

### 법적 준수
- ✅ 교보문고 및 멜론 이용약관 준수
- ✅ 크롤링 시 서버 부담 최소화
  - 책: 요청 간 2초 딜레이
  - 음악: 요청 간 2~5초 랜덤 딜레이
- ✅ 개인적/교육적 목적으로만 사용 (캡스톤 프로젝트)

### 기술적 고려사항
- ✅ 에러 처리 구현 (timeout, 재시도 전략)
- ✅ 중복 제거로 데이터 정확성 확보
  - 책: ISBN 기준
  - 음악: Song ID 기준
- ⚠️ Windows CMD에서 한글 깨짐 (JSON 파일은 UTF-8로 정상)
- ⚠️ 음악 크롤링 시 일부 곡 상세 페이지 timeout 발생 가능 (자동 스킵)

---

## 🔗 관련 링크

- [BeautifulSoup 공식 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests 공식 문서](https://requests.readthedocs.io/)
- [교보문고](https://www.kyobobook.co.kr/)
- [멜론](https://www.melon.com/)

---

## 📄 License

This project is for educational purposes (Capstone Project).

---

## 👥 Team

**캡스톤 프로젝트 - ICSYF Team**

*"I Can See Your Feelings - 감정 기반 정서 관리 플랫폼"*
