# -*- coding: utf-8 -*-
"""
멜론 음악 크롤러 - 감정 기반 음악 추천 시스템
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================================
# 설정 및 상수
# ============================================================================

# 감정별 장르 매핑 (CLAUDE.md 기준)
EMOTION_GENRES = {
    "joy":        ["GN0200", "GN0900"],  # 댄스, POP
    "excitement": ["GN0500", "GN1500"],  # 인디음악, OST
    "normal":     ["GN0500", "GN0800"],  # 인디음악, 포크/블루스
    "sadness":    ["GN0400", "GN0100"],  # R&B/Soul, 발라드
    "anxiety":    ["GN0400", "GN0800"],  # R&B/Soul, 포크/블루스
    "anger":      ["GN0300", "GN0600"]   # 랩/힙합, 록/메탈
}

GENRE_CODES = {
    "GN0100": "발라드",
    "GN0200": "댄스",
    "GN0300": "랩/힙합",
    "GN0400": "R&B/Soul",
    "GN0500": "인디음악",
    "GN0600": "록/메탈",
    "GN0800": "포크/블루스",
    "GN0900": "POP",
    "GN1500": "OST"
}

# 크롤링 설정
MIN_DELAY = 2  # 최소 딜레이 (초)
MAX_DELAY = 5  # 최대 딜레이 (초)
TIMEOUT = 10    # 타임아웃 (초)
MAX_PAGES = 10  # 최대 페이지 수

# Headers (브라우저 위장)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://www.melon.com/genre/song_list.htm?gnrCode=GN0200&steadyYn=Y',
    'Connection': 'keep-alive',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin'
}

# 데이터 저장 경로
DATA_DIR = "data/musics"

# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_session():
    """재시도 전략이 적용된 세션 생성"""
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504]
    )

    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    return session


def random_delay():
    """랜덤 딜레이 (봇 감지 회피)"""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)


def ensure_data_dir():
    """데이터 저장 디렉토리 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def save_to_json(filepath, data):
    """데이터를 JSON 파일로 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 저장 완료: {filepath} ({len(data)}곡)")


# ============================================================================
# 파싱 함수
# ============================================================================

def parse_song_list(row):
    """
    목록 페이지에서 곡 정보 파싱 (6개 항목)

    Args:
        row: BeautifulSoup tr 태그

    Returns:
        dict: 곡 정보 (song_id, title, artist, album, cover_url, detail_url)
    """
    try:
        # Song ID
        checkbox = row.select_one('input[type="checkbox"]')
        song_id = checkbox.get('value', '') if checkbox else None

        if not song_id:
            return None

        # Title
        title_elem = row.select_one('div.ellipsis.rank01 a')
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Artist
        artist_elem = row.select_one('div.ellipsis.rank02 a')
        artist = artist_elem.get_text(strip=True) if artist_elem else ""

        # Album
        album_elem = row.select_one('div.ellipsis.rank03 a')
        album = album_elem.get_text(strip=True) if album_elem else ""

        # Cover URL (고화질로 변환: 180px, quality 100)
        img_elem = row.select_one('img')
        cover_url = img_elem.get('src', '') if img_elem else ""

        # 화질 개선: resize/120 → resize/180, quality/80 → quality/100
        if cover_url:
            cover_url = cover_url.replace('/melon/resize/120/quality/80/optimize',
                                         '/melon/resize/180/quality/100/optimize')

        # Detail URL
        detail_url = f"https://www.melon.com/song/detail.htm?songId={song_id}"

        # 필터링: (Inst.) 또는 (MR) 제외
        if "(Inst.)" in title or "(MR)" in title:
            return None

        return {
            "song_id": song_id,
            "title": title,
            "artist": artist,
            "album": album,
            "cover_url": cover_url,
            "detail_url": detail_url
        }

    except Exception as e:
        print(f"  [WARNING] 곡 파싱 실패: {e}")
        return None


def parse_song_detail(soup):
    """
    상세 페이지에서 추가 정보 파싱 (2개 항목)

    Args:
        soup: BeautifulSoup 객체

    Returns:
        dict: 추가 정보 (genre, dj_tags)
    """
    try:
        # 장르
        genre = ""
        genre_dt = soup.find('dt', string=re.compile('장르'))
        if genre_dt:
            genre_dd = genre_dt.find_next_sibling('dd')
            if genre_dd:
                genre = genre_dd.get_text(strip=True)

        # DJ 태그
        dj_tags = []
        tag_items = soup.find_all('a', class_='tag_item')
        for tag_item in tag_items:
            tag_text = tag_item.get_text(strip=True)
            if tag_text:
                dj_tags.append(tag_text)

        return {
            "genre": genre,
            "dj_tags": dj_tags
        }

    except Exception as e:
        print(f"  [WARNING] 상세 페이지 파싱 실패: {e}")
        return {"genre": "", "dj_tags": []}


# ============================================================================
# 크롤링 함수
# ============================================================================

def crawl_genre_list(session, genre_code):
    """
    장르별 목록 페이지 크롤링 (페이징 지원 - 최대 10페이지)

    Args:
        session: requests.Session 객체
        genre_code: 장르 코드 (예: GN0100)

    Returns:
        list: 곡 정보 리스트
    """
    genre_name = GENRE_CODES.get(genre_code, genre_code)
    print(f"  크롤링 중: {genre_name} ({genre_code})...")

    all_songs = []

    for page_num in range(1, MAX_PAGES + 1):
        try:
            # startIndex 계산 (1페이지=1, 2페이지=51, 3페이지=101, ...)
            start_index = 1 + (page_num - 1) * 50

            # AJAX 페이징 URL 사용 (pageSize, orderBy 파라미터 추가!)
            url = f"https://www.melon.com/genre/song_listPaging.htm?startIndex={start_index}&pageSize=50&gnrCode={genre_code}&dtlGnrCode=&orderBy=NEW&steadyYn=Y"

            random_delay()
            response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                print(f"    [ERROR] 페이지 {page_num} - HTTP {response.status_code} 에러")
                break

            soup = BeautifulSoup(response.text, 'html.parser')

            # tbody 안의 모든 tr 찾기
            tbody = soup.find('tbody')
            if not tbody:
                print(f"    [WARNING] 페이지 {page_num} - tbody 태그를 찾을 수 없습니다")
                break

            song_rows = tbody.find_all('tr')

            # 빈 페이지면 종료
            if len(song_rows) == 0:
                print(f"    페이지 {page_num} - 더 이상 곡이 없습니다")
                break

            page_songs = []
            for row in song_rows:
                song = parse_song_list(row)
                if song:
                    page_songs.append(song)

            all_songs.extend(page_songs)
            print(f"    페이지 {page_num}: {len(page_songs)}곡 수집")

        except Exception as e:
            print(f"    [ERROR] 페이지 {page_num} 크롤링 실패: {e}")
            break

    print(f"  [OK] 총 {len(all_songs)}곡 수집 완료")
    return all_songs


def crawl_song_detail(session, detail_url):
    """
    곡 상세 페이지 크롤링

    Args:
        session: requests.Session 객체
        detail_url: 상세 페이지 URL

    Returns:
        dict: 추가 정보 (genre, dj_tags)
    """
    try:
        random_delay()
        response = session.get(detail_url, headers=HEADERS, timeout=TIMEOUT)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            return {"genre": "", "dj_tags": []}

        soup = BeautifulSoup(response.text, 'html.parser')
        return parse_song_detail(soup)

    except Exception as e:
        print(f"  [WARNING] 상세 페이지 크롤링 실패: {e}")


def crawl_emotion(session, emotion_name, genre_codes):
    """
    한 감정의 모든 장르 크롤링 후 병합

    Args:
        session: requests.Session 객체
        emotion_name: 감정 이름 (예: joy)
        genre_codes: 장르 코드 리스트

    Returns:
        list: 중복 제거된 곡 리스트
    """
    print(f"\n{'='*60}")
    print(f"감정: {emotion_name.upper()}")
    print(f"{'='*60}")

    all_songs = {}  # song_id를 key로 사용 (중복 제거)

    # 1단계: 목록 페이지 크롤링
    for genre_code in genre_codes:
        songs = crawl_genre_list(session, genre_code)

        for song in songs:
            song_id = song['song_id']
            if song_id not in all_songs:
                all_songs[song_id] = song

    print(f"\n1단계 완료: 총 {len(all_songs)}곡 수집 (중복 제거 완료)")

    # 2단계: 상세 페이지 크롤링
    print(f"\n2단계 시작: 상세 페이지 크롤링 중...")
    count = 0
    total = len(all_songs)

    for song_id, song_data in all_songs.items():
        count += 1
        try:
            print(f"  [{count}/{total}] {song_data['title']} - {song_data['artist']}", end=" ")
        except UnicodeEncodeError:
            print(f"  [{count}/{total}] [ID:{song_id}]", end=" ")

        detail = crawl_song_detail(session, song_data['detail_url'])
        song_data.update(detail)

        print("[OK]")

    # 3단계: 장르 중복 제거
    for song in all_songs.values():
        if song.get('genre'):
            genres = [g.strip() for g in song['genre'].split(',')]
            song['genre'] = ', '.join(sorted(set(genres)))

    print(f"\n3단계 완료: 데이터 병합 및 정제 완료")

    return list(all_songs.values())


def crawl_all_emotions(session):
    """전체 6개 감정 크롤링"""
    ensure_data_dir()

    print("\n" + "="*60)
    print("멜론 음악 크롤러 시작")
    print("="*60)

    for emotion_name, genre_codes in EMOTION_GENRES.items():
        songs = crawl_emotion(session, emotion_name, genre_codes)

        # JSON 파일로 저장
        filepath = os.path.join(DATA_DIR, f"{emotion_name}.json")
        save_to_json(filepath, songs)

    print("\n" + "="*60)
    print("모든 크롤링 완료!")
    print("="*60)


# ============================================================================
# 메인 실행
# ============================================================================

def print_usage():
    """사용법 출력"""
    print("""
사용법:
  python crawl_music.py                    # 사용법 출력
  python crawl_music.py joy                # joy 감정만 크롤링
  python crawl_music.py joy sadness        # joy, sadness 크롤링
  python crawl_music.py --full             # 전체 6개 감정 크롤링

감정 목록:
  joy         기쁨 (댄스, POP)
  excitement  설렘 (인디음악, OST)
  normal      보통 (인디음악, 포크/블루스)
  sadness     슬픔 (R&B/Soul, 발라드)
  anxiety     불안 (R&B/Soul, 포크/블루스)
  anger       분노 (랩/힙합, 록/메탈)
""")


def main():
    """메인 함수"""
    import sys

    # 인자 없으면 사용법 출력
    if len(sys.argv) == 1:
        print_usage()
        return

    session = create_session()
    ensure_data_dir()

    try:
        # --full 옵션: 전체 크롤링
        if "--full" in sys.argv:
            print("\n" + "="*60)
            print("전체 6개 감정 크롤링 시작")
            print("="*60)
            crawl_all_emotions(session)
        else:
            # 특정 감정만 크롤링
            emotions_to_crawl = sys.argv[1:]

            # 유효성 검사
            invalid_emotions = [e for e in emotions_to_crawl if e not in EMOTION_GENRES]
            if invalid_emotions:
                print(f"\n[ERROR] 잘못된 감정: {', '.join(invalid_emotions)}")
                print_usage()
                return

            print("\n" + "="*60)
            print(f"선택된 감정 크롤링: {', '.join(emotions_to_crawl)}")
            print("="*60)

            for emotion_name in emotions_to_crawl:
                genre_codes = EMOTION_GENRES[emotion_name]
                songs = crawl_emotion(session, emotion_name, genre_codes)

                # JSON 파일로 저장
                filepath = os.path.join(DATA_DIR, f"{emotion_name}.json")
                save_to_json(filepath, songs)

            print("\n" + "="*60)
            print("크롤링 완료!")
            print("="*60)

    except KeyboardInterrupt:
        print("\n\n크롤링이 중단되었습니다.")
    except Exception as e:
        print(f"\n\n에러 발생: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
