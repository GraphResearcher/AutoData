"""
Search Engine Tool - Tìm kiếm thông tin trên web.
Hỗ trợ Google Search và các search engines khác.
"""

import requests
from googlesearch import search as google_search
from typing import List, Dict, Any
import logging
import time
from urllib.parse import quote_plus

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


class SearchEngineTool:
    """Tool để tìm kiếm thông tin trên web"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })
        self.max_results = config.GOOGLE_SEARCH_MAX_RESULTS
        self.timeout = 30  # Increase timeout to 30 seconds

    def search(self, query: str, num_results: int = 10, search_engine: str = "auto") -> ToolResult:
        """
        Tìm kiếm với query.

        Args:
            query: Search query
            num_results: Số lượng kết quả
            search_engine: "google", "duckduckgo", or "auto" (try both)

        Returns:
            ToolResult với danh sách kết quả
        """
        try:
            logger.info(f"Searching for: {query}")

            # If auto, try multiple engines
            if search_engine == "auto":
                # Try DuckDuckGo first (less likely to be rate limited)
                results = self._search_duckduckgo(query, num_results)

                # If DuckDuckGo fails or returns nothing, try Google
                if not results:
                    logger.info("DuckDuckGo returned no results, trying Google...")
                    results = self._search_google(query, num_results)
            elif search_engine == "google":
                results = self._search_google(query, num_results)
            elif search_engine == "duckduckgo":
                results = self._search_duckduckgo(query, num_results)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported search engine: {search_engine}"
                )

            logger.info(f"Found {len(results)} results for '{query}'")

            return ToolResult(
                success=True,
                data={
                    'query': query,
                    'results': results,
                    'count': len(results),
                    'search_engine': search_engine
                }
            )

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )

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

    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (HTML scraping)"""
        results = []

        try:
            logger.info(f"Searching via DuckDuckGo for: {query}")

            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            # Add more realistic headers
            headers = {
                'User-Agent': config.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = self.session.get(
                search_url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # DuckDuckGo HTML structure
            result_divs = soup.find_all('div', class_='result')

            for idx, div in enumerate(result_divs[:num_results]):
                link_tag = div.find('a', class_='result__a')
                if not link_tag:
                    continue

                url = link_tag.get('href', '')
                title = link_tag.get_text(strip=True)

                snippet_tag = div.find('a', class_='result__snippet')
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''

                if url and title:
                    results.append({
                        'rank': idx + 1,
                        'url': url,
                        'title': title,
                        'snippet': snippet
                    })

            logger.info(f"DuckDuckGo returned {len(results)} results")

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")

        return results

    def search_vietnamese_news(self, query: str, num_results: int = 10) -> ToolResult:
        """
        Tìm kiếm trên các trang tin Việt Nam.

        Args:
            query: Search query
            num_results: Số kết quả

        Returns:
            ToolResult với kết quả từ các trang tin VN
        """
        # Add "site:" operator cho các trang tin VN
        news_sites = [
            'vnexpress.net',
            'tuoitre.vn',
            'thanhnien.vn',
            'dantri.com.vn',
            'vietnamnet.vn'
        ]

        site_query = ' OR '.join([f'site:{site}' for site in news_sites])
        full_query = f"{query} ({site_query})"

        return self.search(full_query, num_results)

    def search_forums(self, query: str, num_results: int = 10) -> ToolResult:
        """
        Tìm kiếm trên các diễn đàn Việt Nam.

        Args:
            query: Search query
            num_results: Số kết quả

        Returns:
            ToolResult với kết quả từ forums
        """
        # Add keywords để tìm forum discussions
        forum_query = f"{query} (thảo luận OR ý kiến OR bình luận OR diễn đàn OR forum)"

        return self.search(forum_query, num_results)

    def search_multiple_queries(self, queries: List[str], num_per_query: int = 5) -> ToolResult:
        """
        Tìm kiếm với nhiều queries.

        Args:
            queries: Danh sách queries
            num_per_query: Số kết quả per query

        Returns:
            ToolResult với tất cả kết quả
        """
        try:
            all_results = []

            for query in queries:
                logger.info(f"Searching query: {query}")
                result = self.search(query, num_per_query)

                if result.success:
                    all_results.extend(result.data['results'])

                # Rate limiting
                time.sleep(2)

            # Remove duplicates by URL
            seen_urls = set()
            unique_results = []
            for result in all_results:
                url = result['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)

            logger.info(f"Total unique results: {len(unique_results)}")

            return ToolResult(
                success=True,
                data={
                    'queries': queries,
                    'results': unique_results,
                    'total_count': len(unique_results)
                }
            )

        except Exception as e:
            logger.error(f"Multiple search error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Multiple search failed: {str(e)}"
            )


# Singleton instance
search_engine_tool = SearchEngineTool()