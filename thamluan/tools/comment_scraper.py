"""
Comment Scraper Tool - Crawl comments/opinions từ các nguồn.
Hỗ trợ scrape từ news sites, forums, và social media.
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re
import logging

from core.config import config
from core.types import ToolResult, Comment

logger = logging.getLogger(__name__)


class CommentScraperTool:
    """Tool để scrape comments từ nhiều nguồn"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })
        self.max_comments = config.MAX_COMMENTS_PER_SOURCE
        self.min_length = config.COMMENT_MIN_LENGTH

    def scrape_comments(self, url: str, source_type: str = "auto") -> ToolResult:
        """
        Scrape comments từ một URL.

        Args:
            url: URL cần scrape
            source_type: "news", "forum", "facebook", "auto" (tự detect)

        Returns:
            ToolResult với danh sách Comments
        """
        try:
            logger.info(f"Scraping comments from: {url}")

            # Auto-detect source type
            if source_type == "auto":
                source_type = self._detect_source_type(url)

            logger.info(f"Detected source type: {source_type}")

            # Scrape based on source type
            if source_type == "news":
                comments = self._scrape_news_comments(url)
            elif source_type == "forum":
                comments = self._scrape_forum_posts(url)
            elif source_type == "facebook":
                comments = self._scrape_facebook_comments(url)
            else:
                comments = self._scrape_generic_comments(url)

            # Filter comments by length
            filtered_comments = [
                c for c in comments
                if len(c.content) >= self.min_length
            ]

            logger.info(f"Scraped {len(filtered_comments)} comments from {url}")

            return ToolResult(
                success=True,
                data={
                    'url': url,
                    'source_type': source_type,
                    'comments': filtered_comments,
                    'count': len(filtered_comments)
                }
            )

        except Exception as e:
            logger.error(f"Error scraping comments: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to scrape comments: {str(e)}"
            )

    def _detect_source_type(self, url: str) -> str:
        """Detect loại source từ URL"""
        url_lower = url.lower()

        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        elif any(news in url_lower for news in ['vnexpress', 'tuoitre', 'thanhnien', 'dantri', 'vietnamnet']):
            return 'news'
        elif 'forum' in url_lower or 'dien-dan' in url_lower:
            return 'forum'
        else:
            return 'generic'

    def _scrape_news_comments(self, url: str) -> List[Comment]:
        """Scrape comments từ trang tin tức"""
        comments = []

        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            # VNExpress comment structure
            if 'vnexpress.net' in url:
                comment_divs = soup.find_all('div', class_=['item_comment', 'comment-item'])

                for div in comment_divs[:self.max_comments]:
                    author_tag = div.find('strong', class_='nickname')
                    author = author_tag.get_text(strip=True) if author_tag else None

                    content_tag = div.find('p', class_='content')
                    if not content_tag:
                        content_tag = div.find('div', class_='full_content')
                    content = content_tag.get_text(strip=True) if content_tag else ""

                    time_tag = div.find('span', class_='time')
                    timestamp_str = time_tag.get_text(strip=True) if time_tag else None

                    if content:
                        comments.append(Comment(
                            source='VNExpress',
                            source_url=url,
                            author=author,
                            content=content,
                            timestamp=self._parse_timestamp(timestamp_str) if timestamp_str else None
                        ))

            # Tuổi Trẻ comment structure
            elif 'tuoitre.vn' in url:
                comment_divs = soup.find_all('div', class_=['comment-item', 'box-comment'])

                for div in comment_divs[:self.max_comments]:
                    author_tag = div.find('strong')
                    author = author_tag.get_text(strip=True) if author_tag else None

                    content_tag = div.find('p', class_='content-comment')
                    content = content_tag.get_text(strip=True) if content_tag else ""

                    if content:
                        comments.append(Comment(
                            source='Tuổi Trẻ',
                            source_url=url,
                            author=author,
                            content=content
                        ))

            # Generic news site comments
            else:
                # Tìm các pattern phổ biến
                comment_patterns = [
                    {'tag': 'div', 'class': 'comment'},
                    {'tag': 'div', 'class': 'comment-body'},
                    {'tag': 'li', 'class': 'comment'},
                    {'tag': 'article', 'class': 'comment'},
                ]

                for pattern in comment_patterns:
                    comment_elements = soup.find_all(pattern['tag'], class_=re.compile(pattern['class']))

                    if comment_elements:
                        for elem in comment_elements[:self.max_comments]:
                            content = elem.get_text(strip=True)
                            if len(content) >= self.min_length:
                                comments.append(Comment(
                                    source='News Site',
                                    source_url=url,
                                    content=content
                                ))
                        break

        except Exception as e:
            logger.warning(f"News comment scraping failed: {str(e)}")

        return comments

    def _scrape_forum_posts(self, url: str) -> List[Comment]:
        """Scrape posts từ diễn đàn"""
        comments = []

        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            # Generic forum structure
            post_patterns = [
                {'tag': 'div', 'class': 'post'},
                {'tag': 'div', 'class': 'message'},
                {'tag': 'div', 'class': 'post-content'},
                {'tag': 'article', 'class': 'post'},
            ]

            for pattern in post_patterns:
                post_elements = soup.find_all(pattern['tag'], class_=re.compile(pattern['class']))

                if post_elements:
                    for elem in post_elements[:self.max_comments]:
                        author_tag = elem.find(['span', 'strong', 'a'], class_=re.compile('author|username|name'))
                        author = author_tag.get_text(strip=True) if author_tag else None

                        # Tìm content
                        content_tag = elem.find(['div', 'p'], class_=re.compile('content|message|text'))
                        if not content_tag:
                            content_tag = elem

                        content = content_tag.get_text(strip=True)

                        if len(content) >= self.min_length:
                            comments.append(Comment(
                                source='Forum',
                                source_url=url,
                                author=author,
                                content=content
                            ))
                    break

        except Exception as e:
            logger.warning(f"Forum scraping failed: {str(e)}")

        return comments

    def _scrape_facebook_comments(self, url: str) -> List[Comment]:
        """
        Scrape Facebook comments (khó vì cần login).
        Sử dụng Selenium và có thể không hoạt động tốt.
        """
        comments = []
        driver = None

        try:
            logger.warning("Facebook scraping có thể không hoạt động tốt do yêu cầu đăng nhập")

            # Setup Selenium
            chrome_options = Options()
            if config.SELENIUM_HEADLESS:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)

            # Wait for comments to load
            time.sleep(5)

            # Scroll to load more comments
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'lxml')

            # Facebook comment structure (thay đổi thường xuyên)
            comment_divs = soup.find_all('div', {'role': 'article'})

            for div in comment_divs[:self.max_comments]:
                content = div.get_text(strip=True)
                if len(content) >= self.min_length:
                    comments.append(Comment(
                        source='Facebook',
                        source_url=url,
                        content=content
                    ))

        except Exception as e:
            logger.warning(f"Facebook scraping failed: {str(e)}")
        finally:
            if driver:
                driver.quit()

        return comments

    def _scrape_generic_comments(self, url: str) -> List[Comment]:
        """Scrape comments từ bất kỳ trang nào (generic approach)"""
        comments = []

        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            # Tìm các elements có thể là comments
            potential_comment_tags = soup.find_all(['div', 'article', 'section', 'li'])

            for tag in potential_comment_tags[:self.max_comments * 2]:
                # Check if có class/id liên quan đến comment
                tag_attrs = ' '.join([str(tag.get('class', '')), str(tag.get('id', ''))])

                if any(keyword in tag_attrs.lower() for keyword in
                       ['comment', 'opinion', 'feedback', 'review', 'binh-luan', 'y-kien']):
                    content = tag.get_text(strip=True)

                    if self.min_length <= len(content) <= 5000:
                        comments.append(Comment(
                            source='Generic',
                            source_url=url,
                            content=content
                        ))

                if len(comments) >= self.max_comments:
                    break

        except Exception as e:
            logger.warning(f"Generic scraping failed: {str(e)}")

        return comments

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string thành datetime"""
        try:
            # Add parsing logic for Vietnamese date formats
            # Ví dụ: "2 giờ trước", "1 ngày trước", "20/10/2024"

            now = datetime.now()

            if 'giờ trước' in timestamp_str or 'hour' in timestamp_str:
                hours = int(re.search(r'\d+', timestamp_str).group())
                return now.replace(hour=now.hour - hours)
            elif 'ngày trước' in timestamp_str or 'day' in timestamp_str:
                days = int(re.search(r'\d+', timestamp_str).group())
                return now.replace(day=now.day - days)
            else:
                # Try to parse as date
                return datetime.strptime(timestamp_str, '%d/%m/%Y')
        except:
            return None

    def scrape_multiple_urls(self, urls: List[str]) -> ToolResult:
        """
        Scrape comments từ nhiều URLs.

        Args:
            urls: Danh sách URLs

        Returns:
            ToolResult với tất cả comments
        """
        try:
            all_comments = []

            for url in urls:
                logger.info(f"Scraping: {url}")
                result = self.scrape_comments(url)

                if result.success:
                    all_comments.extend(result.data['comments'])

                # Rate limiting
                time.sleep(config.RETRY_DELAY)

            logger.info(f"Total scraped comments: {len(all_comments)}")

            return ToolResult(
                success=True,
                data={
                    'urls': urls,
                    'comments': all_comments,
                    'total_count': len(all_comments)
                }
            )

        except Exception as e:
            logger.error(f"Multiple scraping error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Multiple scraping failed: {str(e)}"
            )


# Singleton instance
comment_scraper_tool = CommentScraperTool()