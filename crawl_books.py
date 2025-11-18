# -*- coding: utf-8 -*-
"""
Kyobo Bookstore Crawling System
Emotion-based book recommendation data collection
"""

import time
import json
import os
import requests
from bs4 import BeautifulSoup


# ==================== Configuration ====================

# Emotion-based search keywords
EMOTION_KEYWORDS = {
    'joy': ['유머', '재미있는 소설', '힐링', '따뜻한 에세이', '동기부여'],
    'excitement': ['새로운 시작', '여행 에세이', '영감', '도전', '로맨스 소설'],
    'normal': ['에세이', '일상', '취미', '요리', '소설 베스트셀러'],
    'sadness': ['위로', '공감', '치유', '성장 소설', '괜찮아'],
    'anxiety': ['용기', '자존감', '극복', '심리', '안정'],
    'anger': ['마음챙김', '명상', '평온', '스트레스 해소', '감정 조절']
}

# Crawling settings
PAGES_PER_KEYWORD = 3
SORT_TYPES = ['best', 'sale']  # popularity, sales
DELAY_SECONDS = 2

# URL pattern
SEARCH_URL_TEMPLATE = "https://search.kyobobook.co.kr/search?keyword={keyword}&target=kyobo&sort={sort}&page={page}"

# Request headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


# ==================== Parsing Functions ====================

def parse_book_item(item):
    """
    Parse book information from a single prod_item element

    Args:
        item: BeautifulSoup element (li.prod_item)

    Returns:
        dict: Book information or None if parsing fails
    """
    try:
        book = {}

        # Product ID
        pid_input = item.select_one('input.result_checkbox')
        if pid_input:
            book['product_id'] = pid_input.get('data-pid', '')
            book['isbn'] = pid_input.get('data-bid', '')

        # Title
        title_span = item.select_one('span[id^="cmdtName_"]')
        if title_span:
            book['title'] = title_span.get_text(strip=True)

        # Author
        author_link = item.select_one('a.author.rep')
        if author_link:
            book['author'] = author_link.get_text(strip=True)
        else:
            book['author'] = ''

        # Publisher
        publisher_link = item.select_one('div.prod_publish a.text')
        if publisher_link:
            book['publisher'] = publisher_link.get_text(strip=True)
        else:
            book['publisher'] = ''

        # Publication date
        pub_date = item.select_one('div.prod_publish span.date')
        if pub_date:
            book['pub_date'] = pub_date.get_text(strip=True)
        else:
            book['pub_date'] = ''

        # Subtitle (부제목)
        subtitle_span = item.select_one('div.prod_desc_info span.prod_desc')
        if subtitle_span:
            book['subtitle'] = subtitle_span.get_text(strip=True)
        else:
            book['subtitle'] = ''

        # Price (정가)
        price_normal = item.select_one('span.price_normal s.val')
        if price_normal:
            book['price'] = price_normal.get_text(strip=True)
        else:
            # Fallback to regular price if no discount
            price_val = item.select_one('span.price span.val')
            if price_val:
                book['price'] = price_val.get_text(strip=True) + '원'
            else:
                book['price'] = ''

        # Tags (태그)
        tag_links = item.select('div.tag_wrap.size_sm a.tag')
        if tag_links:
            # Remove '#' prefix from tags
            book['tags'] = [tag.get_text(strip=True).replace('#', '') for tag in tag_links]
        else:
            book['tags'] = []

        # Product link (for detail page)
        prod_link = item.select_one('a.prod_link, a.prod_info')
        if prod_link:
            book['detail_url'] = prod_link.get('href', '')

        # Check if we got essential info
        if 'title' in book and book['title']:
            return book
        else:
            return None

    except Exception as e:
        print(f"[WARN] Failed to parse item: {e}")
        return None


# ==================== Crawling Functions ====================

def crawl_keyword(keyword, sort_type='best', page=1):
    """
    Crawl book list for specific keyword, sort type, and page

    Args:
        keyword (str): Search keyword
        sort_type (str): Sort type ('best' or 'sale')
        page (int): Page number

    Returns:
        list: List of book information
    """
    url = SEARCH_URL_TEMPLATE.format(keyword=keyword, sort=sort_type, page=page)
    print(f"Crawling: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Check if we got HTML content
        if response.text:
            print(f"[OK] Page loaded: {len(response.text)} bytes")

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all book items
            items = soup.select('li.prod_item')
            print(f"[OK] Found {len(items)} book items")

            books = []
            for item in items:
                book = parse_book_item(item)
                if book:
                    books.append(book)

            print(f"[OK] Successfully parsed {len(books)} books")
            return books
        else:
            print("[FAIL] Empty response")
            return []

    except Exception as e:
        print(f"[FAIL] Crawling failed: {e}")
        return []


# ==================== Data Management ====================

def remove_duplicates(books):
    """
    Remove duplicate books based on ISBN (or title+author if ISBN not available)

    Args:
        books (list): List of book dictionaries

    Returns:
        list: Deduplicated book list
    """
    seen = set()
    unique_books = []

    for book in books:
        # Use ISBN as primary key
        isbn = book.get('isbn', '')

        # Fallback: use title+author combination if no ISBN
        if not isbn:
            key = f"{book.get('title', '')}_{book.get('author', '')}"
        else:
            key = isbn

        if key not in seen:
            seen.add(key)
            unique_books.append(book)

    removed = len(books) - len(unique_books)
    if removed > 0:
        print(f"[INFO] Removed {removed} duplicate books")

    return unique_books


def save_to_json(books, filename):
    """
    Save book list to JSON file

    Args:
        books (list): List of book dictionaries
        filename (str): Output filename (e.g., 'joy.json')
    """
    # Create data directory if not exists
    os.makedirs('data', exist_ok=True)

    filepath = os.path.join('data', filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved {len(books)} books to {filepath}")
    except Exception as e:
        print(f"[FAIL] Failed to save JSON: {e}")


# ==================== Orchestration Functions ====================

def crawl_emotion(emotion_name, keywords):
    """
    Crawl books for a specific emotion with multiple keywords

    Args:
        emotion_name (str): Emotion name (e.g., 'joy', 'sadness')
        keywords (list): List of search keywords

    Returns:
        list: All books collected for this emotion (deduplicated)
    """
    print(f"\n{'='*60}")
    print(f"Crawling emotion: {emotion_name}")
    print(f"Keywords: {keywords}")
    print(f"{'='*60}")

    all_books = []

    for keyword in keywords:
        print(f"\n[Keyword] {keyword}")

        # Crawl with both sort types
        for sort_type in SORT_TYPES:
            print(f"  [Sort] {sort_type}")

            # Crawl multiple pages
            for page in range(1, PAGES_PER_KEYWORD + 1):
                books = crawl_keyword(keyword, sort_type, page)
                all_books.extend(books)

                # Delay between requests (be polite!)
                time.sleep(DELAY_SECONDS)

    # Remove duplicates
    print(f"\n[Summary] Total books before deduplication: {len(all_books)}")
    unique_books = remove_duplicates(all_books)
    print(f"[Summary] Unique books after deduplication: {len(unique_books)}")

    return unique_books


def crawl_all_emotions():
    """
    Crawl books for all emotions and save to separate JSON files
    """
    print("=" * 60)
    print("FULL CRAWLING - ALL EMOTIONS")
    print("=" * 60)

    for emotion_key, keywords in EMOTION_KEYWORDS.items():
        books = crawl_emotion(emotion_key, keywords)

        # Save to JSON file
        filename = f"{emotion_key}.json"
        save_to_json(books, filename)

        print(f"\n[DONE] {emotion_key}: {len(books)} books saved\n")

    print("=" * 60)
    print("ALL EMOTIONS CRAWLING COMPLETED!")
    print("=" * 60)


# ==================== Main Execution ====================

def main():
    """Main execution function"""
    import sys

    # Available emotions
    available_emotions = list(EMOTION_KEYWORDS.keys())

    if len(sys.argv) > 1:
        if sys.argv[1] == '--full':
            # Full crawling mode: all emotions
            crawl_all_emotions()
        else:
            # Specific emotions mode
            emotions_to_crawl = sys.argv[1:]

            # Validate emotions
            invalid = [e for e in emotions_to_crawl if e not in available_emotions]
            if invalid:
                print("=" * 60)
                print(f"ERROR: Invalid emotion(s): {', '.join(invalid)}")
                print(f"\nAvailable emotions: {', '.join(available_emotions)}")
                print("=" * 60)
                return

            # Crawl selected emotions
            print("=" * 60)
            print(f"CRAWLING SELECTED EMOTIONS: {', '.join(emotions_to_crawl)}")
            print("=" * 60)

            for emotion in emotions_to_crawl:
                keywords = EMOTION_KEYWORDS[emotion]
                books = crawl_emotion(emotion, keywords)
                save_to_json(books, f'{emotion}.json')
                print(f"\n[DONE] {emotion}: {len(books)} books saved\n")

            print("=" * 60)
            print("SELECTED EMOTIONS CRAWLING COMPLETED!")
            print("=" * 60)
    else:
        # Show usage
        print("=" * 60)
        print("Kyobo Bookstore Crawler - Usage")
        print("=" * 60)
        print("\nUsage:")
        print("  python crawl_books.py [emotions...]")
        print("  python crawl_books.py --full")
        print(f"\nAvailable emotions:")
        print(f"  {', '.join(available_emotions)}")
        print(f"\nExamples:")
        print(f"  python crawl_books.py joy")
        print(f"  python crawl_books.py sadness anxiety")
        print(f"  python crawl_books.py --full")
        print("=" * 60)


if __name__ == "__main__":
    main()
