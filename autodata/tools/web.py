# autodata/tools/web.py
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_page_content(url: str) -> str:
    """Fetch the HTML content of a webpage."""
    try:
        logger.info(f"Fetching page: {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        html = response.text
        logger.info(f"Fetched {len(html)} characters from {url}")
        return html
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None
