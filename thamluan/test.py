"""
Debug search engines để xem vấn đề ở đâu
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def test_duckduckgo(query):
    """Test DuckDuckGo search"""
    print("\n" + "=" * 80)
    print(f"Testing DuckDuckGo: {query}")
    print("=" * 80)

    # Try HTML version
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    print(f"\n1. URL: {search_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        print(f"2. Status: {response.status_code}")
        print(f"3. Content-Length: {len(response.text)}")

        # Save HTML for inspection
        with open('ddg_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("4. ✅ Saved response to ddg_response.html")

        # Parse
        soup = BeautifulSoup(response.text, 'lxml')

        # Try different selectors
        print("\n5. Trying different selectors:")

        # Method 1: result class
        results1 = soup.find_all('div', class_='result')
        print(f"   - div.result: {len(results1)}")

        # Method 2: links class
        results2 = soup.find_all('div', class_='links_main')
        print(f"   - div.links_main: {len(results2)}")

        # Method 3: web-result
        results3 = soup.find_all('div', class_='web-result')
        print(f"   - div.web-result: {len(results3)}")

        # Method 4: All divs with result in class name
        results4 = soup.find_all('div', class_=lambda x: x and 'result' in x.lower())
        print(f"   - div[class*='result']: {len(results4)}")

        # Method 5: Find all links
        all_links = soup.find_all('a', href=True)
        print(f"   - All <a> tags: {len(all_links)}")

        # Show first few links
        print("\n6. Sample links:")
        for i, link in enumerate(all_links[:10], 1):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:50]
            if href and not href.startswith(('#', 'javascript:', '/')):
                print(f"   {i}. {text}")
                print(f"      -> {href[:80]}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_google(query):
    """Test Google search"""
    print("\n" + "=" * 80)
    print(f"Testing Google: {query}")
    print("=" * 80)

    search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=vi"
    print(f"\n1. URL: {search_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'vi-VN,vi;q=0.9',
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        print(f"2. Status: {response.status_code}")
        print(f"3. Content-Length: {len(response.text)}")

        # Save HTML
        with open('google_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("4. ✅ Saved response to google_response.html")

        # Parse
        soup = BeautifulSoup(response.text, 'lxml')

        print("\n5. Trying different selectors:")

        # Method 1: div.g
        results1 = soup.find_all('div', class_='g')
        print(f"   - div.g: {len(results1)}")

        # Method 2: search results
        results2 = soup.find_all('div', {'data-sokoban-container': True})
        print(f"   - div[data-sokoban-container]: {len(results2)}")

        # Method 3: All h3
        results3 = soup.find_all('h3')
        print(f"   - h3 tags: {len(results3)}")

        # Show sample
        print("\n6. Sample results:")
        for i, h3 in enumerate(results3[:5], 1):
            print(f"   {i}. {h3.get_text(strip=True)}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_alternative_search(query):
    """Test alternative search using searx"""
    print("\n" + "=" * 80)
    print(f"Testing Alternative Search: {query}")
    print("=" * 80)

    # Use public SearX instance
    search_url = f"https://searx.be/search?q={quote_plus(query)}&format=json&language=vi"
    print(f"\n1. URL: {search_url}")

    try:
        response = requests.get(search_url, timeout=30)
        print(f"2. Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"3. Results: {len(results)}")

            print("\n4. Sample results:")
            for i, result in enumerate(results[:5], 1):
                print(f"   {i}. {result.get('title', 'No title')}")
                print(f"      {result.get('url', 'No URL')}")

            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    query = "Luật Khoa học Công nghệ 2025 ý kiến"

    print("=" * 80)
    print("Search Engine Debug Tool")
    print("=" * 80)
    print(f"\nQuery: {query}")

    # Test DuckDuckGo
    ddg_ok = test_duckduckgo(query)

    # Test Google
    google_ok = test_google(query)

    # Test alternative
    alt_ok = test_alternative_search(query)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"DuckDuckGo: {'✅ OK' if ddg_ok else '❌ FAILED'}")
    print(f"Google: {'✅ OK' if google_ok else '❌ FAILED'}")
    print(f"Alternative (SearX): {'✅ OK' if alt_ok else '❌ FAILED'}")
    print("\nCheck the HTML files saved for details:")
    print("  - ddg_response.html")
    print("  - google_response.html")
    print("=" * 80)


if __name__ == "__main__":
    main()





 def _search_google(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Google (via googlesearch-python)"""
        results = []

        try:
            logger.info(f"Searching via Google for: {query}")

            # Use googlesearch library with increased timeout
            search_results = google_search(
                query,
                num_results=num_results,
                lang='vi',
                sleep_interval=3,  # Increase delay to avoid rate limiting
                timeout=30  # Increase timeout
            )

            for idx, url in enumerate(search_results):
                results.append({
                    'rank': idx + 1,
                    'url': url,
                    'title': '',  # googlesearch-python doesn't return title
                    'snippet': ''
                })

                if len(results) >= num_results:
                    break

        except Exception as e:
            logger.warning(f"Google search failed: {str(e)}")
            # Try fallback method
            logger.info("Trying fallback search method...")
            results = self._search_google_fallback(query, num_results)

        return results

    def _search_google_fallback(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Fallback Google search bằng scraping (basic)"""
        results = []

        try:
            from bs4 import BeautifulSoup

            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}&hl=vi"

            response = self.session.get(search_url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Parse search results
            search_divs = soup.find_all('div', class_='g')

            for idx, div in enumerate(search_divs[:num_results]):
                link_tag = div.find('a')
                if not link_tag:
                    continue

                url = link_tag.get('href', '')
                if not url.startswith('http'):
                    continue

                title_tag = div.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else ''

                snippet_tag = div.find('div', class_=['VwiC3b', 'yXK7lf'])
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''

                results.append({
                    'rank': idx + 1,
                    'url': url,
                    'title': title,
                    'snippet': snippet
                })

        except Exception as e:
            logger.error(f"Google fallback search failed: {str(e)}")

        return results