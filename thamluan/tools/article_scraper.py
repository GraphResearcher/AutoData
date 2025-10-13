import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import logging
import time

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)

class Article:
    """Đại diện cho một bài báo"""
    def __init__(
        self,
        url: str,
        title: str = "",
        content: str = "",
        source: str = "",
        published_date: datetime = None,
        author: str = "",
        summary: str = ""
    ):
        self.url = url
        self.title = title
        self.content = content
        self.source = source
        self.published_date = published_date or datetime.now()
        self.author = author
        self.summary = summary

    def to_dict(self) -> Dict:
        return {
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'author': self.author,
            'summary': self.summary,
            'content_length': len(self.content),
            'word_count': len(self.content.split())
        }

class ArticleScraperTool:
    """Tool để scrape nội dung bài báo"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
        self.processed_duplicates = set()  # Giảm log duplicate lặp lại

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        return "No Title"

    def _extract_content(self, soup: BeautifulSoup, url: str) -> str:
        paragraphs = soup.find_all('p')
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)
        return text.strip() if text else ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        author_meta = soup.find('meta', attrs={'name':'author'})
        if author_meta and author_meta.get('content'):
            return author_meta['content'].strip()
        return ""

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        desc_meta = soup.find('meta', attrs={'name':'description'})
        if desc_meta and desc_meta.get('content'):
            return desc_meta['content'].strip()
        return ""

    def _detect_source(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc

    def scrape_article(self, url: str, source: str = "") -> ToolResult:
        try:
            logger.info(f"Scraping article: {url}")
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'lxml')
            title = self._extract_title(soup, url)
            content = self._extract_content(soup, url)
            author = self._extract_author(soup)
            summary = self._extract_summary(soup)
            if not source:
                source = self._detect_source(url)

            article = Article(
                url=url, title=title, content=content,
                source=source, author=author, summary=summary
            )

            logger.info(f"✅ Scraped article: {title[:50]}... ({len(content)} chars)")
            return ToolResult(success=True, data={'article': article})

        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return ToolResult(success=False, error=f"Failed to scrape article: {str(e)}")

    def scrape_multiple_articles(self, urls: List[str], existing_urls: set = None) -> ToolResult:
        try:
            existing_urls = existing_urls or set()
            articles = []
            failed = 0
            seen_urls = set(existing_urls)

            for i, url in enumerate(urls, 1):
                if url in seen_urls:
                    if url not in self.processed_duplicates:
                        logger.warning(f"Skipping duplicate URL: {url}")
                        self.processed_duplicates.add(url)
                    continue

                result = self.scrape_article(url)
                if result.success:
                    articles.append(result.data['article'])
                    seen_urls.add(url)
                else:
                    logger.warning(f"Failed to scrape {url}: {result.error}")
                    failed += 1

                if i < len(urls):
                    time.sleep(config.RETRY_DELAY)

            logger.info(f"✅ Scraped {len(articles)} articles ({failed} failed)")
            return ToolResult(success=True, data={'articles': articles, 'count': len(articles), 'failed': failed})

        except Exception as e:
            logger.error(f"Multiple article scraping error: {str(e)}")
            return ToolResult(success=False, error=f"Multiple scraping failed: {str(e)}")

# Singleton instance
article_scraper_tool = ArticleScraperTool()