"""
Direct News Search Tool - Tìm kiếm trực tiếp trên các trang tin Việt Nam
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from typing import List, Dict, Any
import logging

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


class DirectNewsSearchTool:
    """Tool tìm kiếm trực tiếp trên các trang tin Việt Nam"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        })

        # Danh sách website hỗ trợ tìm kiếm
        self.news_sites = {
            'vnexpress': {
                'name': 'VNExpress',
                'search_url': 'https://timkiem.vnexpress.net/?q={query}&media_type=all',
                'parser': self._parse_vnexpress
            },
            'tuoitre': {
                'name': 'Tuổi Trẻ',
                'search_url': 'https://tuoitre.vn/tim-kiem.htm?keywords={query}',
                'parser': self._parse_tuoitre
            },
            'thanhnien': {
                'name': 'Thanh Niên',
                'search_url': 'https://thanhnien.vn/tim-kiem/?keywords={query}',
                'parser': self._parse_thanhnien
            },
            'dantri': {
                'name': 'Dân Trí',
                'search_url': 'https://dantri.com.vn/tim-kiem.htm?q={query}',
                'parser': self._parse_dantri
            },
            'nhandan': {
                'name': 'Nhân Dân',
                'search_url': 'https://nhandan.vn/tim-kiem?keywords={query}',
                'parser': self._parse_nhandan
            },
            'mst': {
                'name': 'Bộ KH&CN',
                'search_url': 'https://mst.gov.vn/tra-cuu/Pages/timkiem.aspx?keyword={query}',
                'parser': self._parse_mst
            },
        }

    # =====================================================================
    # MAIN SEARCH FUNCTION
    # =====================================================================
    def search_all_sites(self, query: str, max_results_per_site: int = 5) -> ToolResult:
        """Tìm kiếm trên tất cả trang báo"""
        try:
            logger.info(f"Searching directly on news sites for: {query}")
            all_results = []

            for site_key, site_info in self.news_sites.items():
                try:
                    logger.info(f"Searching on {site_info['name']}...")
                    results = self._search_site(site_key, query, max_results_per_site)
                    all_results.extend(results)
                    logger.info(f"  → Found {len(results)} results on {site_info['name']}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to search {site_info['name']}: {str(e)}")

            logger.info(f"Total results from all sites: {len(all_results)}")

            return ToolResult(
                success=True,
                data={
                    'query': query,
                    'results': all_results,
                    'count': len(all_results),
                    'method': 'direct_news_search'
                }
            )

        except Exception as e:
            logger.error(f"Direct news search error: {str(e)}")
            return ToolResult(success=False, error=f"Direct news search failed: {str(e)}")

    # =====================================================================
    # SITE SEARCH HANDLER
    # =====================================================================
    def _search_site(self, site_key: str, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Tìm kiếm một trang cụ thể"""
        site_info = self.news_sites[site_key]
        search_url = site_info['search_url'].format(query=quote_plus(query))
        parser = site_info['parser']

        try:
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'lxml')
            results = parser(soup, site_info['name'])

            return results[:max_results]
        except Exception as e:
            logger.error(f"Error searching {site_info['name']}: {str(e)}")
            return []

    # =====================================================================
    # PARSERS
    # =====================================================================
    def _parse_vnexpress(self, soup: BeautifulSoup, source: str) -> List[Dict[str, Any]]:
        results = []
        for article in soup.find_all('article', class_='item-news'):
            try:
                link = article.find('a')
                if not link:
                    continue
                url = link.get('href', '')
                title = link.get('title', '') or link.get_text(strip=True)
                desc = article.find('p', class_='description')
                snippet = desc.get_text(strip=True) if desc else ''
                results.append({'url': url, 'title': title, 'snippet': snippet, 'source': source})
            except Exception:
                continue
        return results

    def _parse_tuoitre(self, soup: BeautifulSoup, source: str) -> List[Dict[str, Any]]:
        results = []
        for article in soup.find_all('div', class_='box-category-item'):
            try:
                link = article.find('a', class_='box-category-link-title')
                if not link:
                    continue
                url = urljoin('https://tuoitre.vn', link.get('href', ''))
                title = link.get('title', '') or link.get_text(strip=True)
                desc = article.find('p')
                snippet = desc.get_text(strip=True) if desc else ''
                results.append({'url': url, 'title': title, 'snippet': snippet, 'source': source})
            except Exception:
                continue
        return results

    def _parse_thanhnien(self, soup: BeautifulSoup, source: str) -> List[Dict[str, Any]]:
        results = []
        for article in soup.find_all('article'):
            try:
                link = article.find('a')
                if not link:
                    continue
                url = urljoin('https://thanhnien.vn', link.get('href', ''))
                title_tag = article.find('h2') or article.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else ''
                snippet_tag = article.find('p')
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                if url and title:
                    results.append({'url': url, 'title': title, 'snippet': snippet, 'source': source})
            except Exception:
                continue
        return results

    def _parse_dantri(self, soup: BeautifulSoup, source: str) -> List[Dict[str, Any]]:
        results = []
        for article in soup.find_all('article'):
            try:
                link = article.find('a', class_='article-title') or article.find('a')
                if not link:
                    continue
                url = urljoin('https://dantri.com.vn', link.get('href', ''))
                title = link.get('title', '') or link.get_text(strip=True)
                snippet_tag = article.find('div', class_='article-excerpt')
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                results.append({'url': url, 'title': title, 'snippet': snippet, 'source': source})
            except Exception:
                continue
        return results

    def _parse_nhandan(self, soup: BeautifulSoup, source: str) -> List[Dict[str, Any]]:
        """Parser cho Báo Nhân Dân"""
        results = []
        articles = soup.find_all('div', class_='box-content')
        for article in articles:
            try:
                link = article.find('a')
                if not link:
                    continue
                url = urljoin('https://nhandan.vn', link.get('href', ''))
                title = link.get_text(strip=True)
                desc = article.find('div', class_='box-des')
                snippet = desc.get_text(strip=True) if desc else ''
                results.append({'url': url, 'title': title, 'snippet': snippet, 'source': source})
            except Exception:
                continue
        return results

    def _parse_mst(self, soup: BeautifulSoup, source: str) -> List[Dict[str, Any]]:
        """Parser cho mst.gov.vn"""
        results = []
        articles = soup.find_all('div', class_='item') or soup.find_all('li')
        for article in articles:
            try:
                link = article.find('a')
                if not link:
                    continue
                url = urljoin('https://mst.gov.vn', link.get('href', ''))
                title = link.get_text(strip=True)
                desc = article.find('p') or article.find('div', class_='desc')
                snippet = desc.get_text(strip=True) if desc else ''
                results.append({'url': url, 'title': title, 'snippet': snippet, 'source': source})
            except Exception:
                continue
        return results


# Singleton instance
direct_news_search_tool = DirectNewsSearchTool()
