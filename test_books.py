# -*- coding: utf-8 -*-
"""
Test crawling script - Test cover_image_url feature
Crawl: keyword="유머", target=kyobo, sort=best, page=1
"""

import time
import json
import os
import requests
from bs4 import BeautifulSoup


# ==================== Configuration ====================

SEARCH_URL = "https://search.kyobobook.co.kr/search?keyword=유머&target=kyobo&sort=best&page=1"

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

        # Cover image URL (construct from ISBN)
        if book.get('isbn'):
            book['cover_image_url'] = f"https://contents.kyobobook.co.kr/sih/fit-in/300x0/pdt/{book['isbn']}.jpg"
        else:
            book['cover_image_url'] = ''

        # Check if we got essential info
        if 'title' in book and book['title']:
            return book
        else:
            return None

    except Exception as e:
        print(f"[WARN] Failed to parse item: {e}")
        return None


# ==================== Crawling Functions ====================

def test_crawl():
    """
    Test crawl: keyword="유머", target=kyobo, sort=best, page=1

    Returns:
        list: List of book information
    """
    print("=" * 60)
    print("TEST CRAWLING")
    print(f"URL: {SEARCH_URL}")
    print("=" * 60)

    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=10)
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


def save_to_json(books, filename='test_books.json'):
    """
    Save book list to JSON file

    Args:
        books (list): List of book dictionaries
        filename (str): Output filename
    """
    # Create data/books directory if not exists
    os.makedirs('data/books', exist_ok=True)

    filepath = os.path.join('data', 'books', filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved {len(books)} books to {filepath}")
        print(f"\n[Sample] First book:")
        if books:
            print(json.dumps(books[0], ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[FAIL] Failed to save JSON: {e}")


# ==================== Main Execution ====================

if __name__ == "__main__":
    books = test_crawl()

    if books:
        save_to_json(books)
        print("\n" + "=" * 60)
        print(f"TEST COMPLETED: {len(books)} books crawled")
        print("=" * 60)
    else:
        print("\n[FAIL] No books crawled")
