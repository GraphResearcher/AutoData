"""
Web Crawler Tool - Crawl nội dung từ web pages.
Hỗ trợ cả static và dynamic content (Selenium).
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional, Dict, List, Any
import time
from urllib.parse import urljoin, urlparse
import re
import logging

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


class WebCrawlerTool:
    """Tool để crawl nội dung từ web pages"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def crawl_url(self, url: str, use_selenium: bool = False) -> ToolResult:
        """
        Crawl nội dung từ một URL.

        Args:
            url: URL cần crawl
            use_selenium: Có dùng Selenium cho dynamic content không

        Returns:
            ToolResult với data chứa thông tin page
        """
        try:
            logger.info(f"Crawling URL: {url} | Selenium: {use_selenium}")

            if use_selenium:
                return self._crawl_with_selenium(url)
            else:
                return self._crawl_with_requests(url)

        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to crawl {url}: {str(e)}"
            )

    def _crawl_with_requests(self, url: str) -> ToolResult:
        """Crawl với requests (cho static content)"""
        try:
            response = self.session.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'lxml')

            # Extract thông tin cơ bản
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ""

            # Remove script và style tags
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            text_content = main_content.get_text(separator='\n', strip=True) if main_content else ""

            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                link_text = link.get_text(strip=True)
                if link_text and absolute_url:
                    links.append({
                        'url': absolute_url,
                        'text': link_text
                    })

            # Find PDF links - improved filtering
            pdf_links = self._filter_pdf_links(links, url)

            data = {
                'url': url,
                'title': title_text,
                'content': text_content,
                'links': links,
                'pdf_links': pdf_links,
                'status_code': response.status_code,
                'content_length': len(text_content),
            }

            logger.info(f"Successfully crawled {url} | PDF links found: {len(pdf_links)}")

            return ToolResult(
                success=True,
                data=data,
                metadata={'method': 'requests'}
            )

        except Exception as e:
            logger.error(f"Requests crawl failed: {str(e)}")
            raise

    def _crawl_with_selenium(self, url: str) -> ToolResult:
        """Crawl với Selenium (cho dynamic content)"""
        driver = None
        try:
            # Setup Chrome options
            chrome_options = Options()
            if config.SELENIUM_HEADLESS:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={config.USER_AGENT}')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)

            # Wait for page load
            WebDriverWait(driver, config.SELENIUM_WAIT_TIME).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for dynamic content
            time.sleep(2)

            # Get page source và parse với BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'lxml')

            title = driver.title

            # Remove unnecessary elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            text_content = main_content.get_text(separator='\n', strip=True) if main_content else ""

            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                link_text = link.get_text(strip=True)
                if link_text and absolute_url:
                    links.append({
                        'url': absolute_url,
                        'text': link_text
                    })

            # Find PDF links - improved filtering
            pdf_links = self._filter_pdf_links(links, url)

            data = {
                'url': url,
                'title': title,
                'content': text_content,
                'links': links,
                'pdf_links': pdf_links,
                'content_length': len(text_content),
            }

            logger.info(f"Successfully crawled {url} with Selenium | PDF links found: {len(pdf_links)}")

            return ToolResult(
                success=True,
                data=data,
                metadata={'method': 'selenium'}
            )

        except Exception as e:
            logger.error(f"Selenium crawl failed: {str(e)}")
            raise
        finally:
            if driver:
                driver.quit()

    def _filter_pdf_links(self, links: List[Dict], base_url: str) -> List[Dict]:
        """
        Filter và validate PDF links.
        Loại bỏ anchor links và chỉ giữ actual PDF URLs.
        """
        pdf_links = []

        for link in links:
            link_url = link['url']
            link_text = link['text'].lower()

            # Skip anchor links
            if '#' in link_url and not link_url.lower().endswith('.pdf'):
                continue

            # Check if URL ends with .pdf
            if link_url.lower().endswith('.pdf'):
                pdf_links.append(link)
                continue

            # Check for download/files paths with PDF
            if any(path in link_url.lower() for path in ['/download/', '/files/', '/uploads/']):
                if '.pdf' in link_url.lower() or 'pdf' in link_text:
                    pdf_links.append(link)
                    continue

            # Check text mentions PDF and URL looks legitimate
            if 'pdf' in link_text or 'tải về' in link_text or 'download' in link_text.lower():
                # Verify URL is not just an anchor
                if not link_url.startswith('#') and link_url != base_url:
                    pdf_links.append(link)

        return pdf_links

    def find_pdf_links(self, url: str) -> ToolResult:
        """
        Tìm tất cả PDF links từ một trang web.
        Sử dụng nhiều strategies để tìm.

        Args:
            url: URL cần tìm PDF links

        Returns:
            ToolResult với danh sách PDF links
        """
        # Try with requests first
        result = self.crawl_url(url, use_selenium=False)

        if not result.success:
            return result

        pdf_links = result.data.get('pdf_links', [])

        # Nếu không tìm thấy, thử với Selenium
        if not pdf_links:
            logger.info("No PDF links found with requests, trying Selenium...")
            result = self.crawl_url(url, use_selenium=True)
            pdf_links = result.data.get('pdf_links', [])

        # Nếu vẫn không có, thử tìm embedded PDFs
        if not pdf_links:
            logger.info("Searching for embedded PDF links in page source...")
            embedded_pdfs = self._find_embedded_pdf_links(url)
            if embedded_pdfs:
                pdf_links.extend(embedded_pdfs)

        logger.info(f"Total PDF links found: {len(pdf_links)}")

        return ToolResult(
            success=True,
            data={'pdf_links': pdf_links, 'count': len(pdf_links)},
            metadata={'source_url': url}
        )

    def _find_embedded_pdf_links(self, url: str) -> List[Dict]:
        """Tìm PDF links embedded trong page (iframe, object, embed tags)"""
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'lxml')

            pdf_links = []

            # Check iframe sources
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '')
                if src and '.pdf' in src.lower():
                    full_url = urljoin(url, src)
                    pdf_links.append({
                        'url': full_url,
                        'text': 'Embedded PDF (iframe)'
                    })

            # Check object/embed tags
            for tag in soup.find_all(['object', 'embed']):
                src = tag.get('data') or tag.get('src', '')
                if src and '.pdf' in src.lower():
                    full_url = urljoin(url, src)
                    pdf_links.append({
                        'url': full_url,
                        'text': 'Embedded PDF (object)'
                    })

            # Check anchor tags with onclick events
            for a in soup.find_all('a', onclick=True):
                onclick = a.get('onclick', '')
                # Look for PDF URLs in onclick
                pdf_matches = re.findall(r'["\']([^"\']*\.pdf[^"\']*)["\']', onclick)
                for match in pdf_matches:
                    full_url = urljoin(url, match)
                    pdf_links.append({
                        'url': full_url,
                        'text': a.get_text(strip=True) or 'PDF from onclick'
                    })

            logger.info(f"Found {len(pdf_links)} embedded PDF links")
            return pdf_links

        except Exception as e:
            logger.error(f"Error finding embedded PDFs: {str(e)}")
            return []

    def extract_text_from_url(self, url: str) -> ToolResult:
        """
        Extract text content từ URL.

        Args:
            url: URL cần extract text

        Returns:
            ToolResult với text content
        """
        result = self.crawl_url(url)

        if not result.success:
            return result

        content = result.data.get('content', '')

        return ToolResult(
            success=True,
            data={'content': content, 'length': len(content)},
            metadata={'source_url': url}
        )


# Singleton instance
web_crawler_tool = WebCrawlerTool()