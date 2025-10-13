"""
autodata.tools.crawler
Heuristic crawler to extract comments or comment-like paragraphs from an article page.
"""
import logging
from typing import List, Dict

from bs4 import BeautifulSoup

from .web import get_page_content

logger = logging.getLogger(__name__)


def crawl_comments_from_url(url: str, max_items: int = 200) -> List[Dict]:
    """
    Crawl a page and try to extract comment-like text blocks heuristically.
    Returns list of {'author': Optional[str], 'text': str, 'meta': dict}.
    """
    html = get_page_content(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    collected = []

    selectors = [
        ".comment", ".comments", "[id*=comment]", "[class*=comment]",
        ".article-comment", ".comment-body", ".cmt", ".fb-comments",
        ".reply", ".comment-wrap", ".comment-list"
    ]

    for sel in selectors:
        nodes = soup.select(sel)
        for node in nodes:
            text = node.get_text(" ", strip=True)
            if text and len(text) > 30:
                collected.append({"author": None, "text": text, "meta": {"selector": sel}})
                if len(collected) >= max_items:
                    return collected

    # Fallback: collect <p> under main article container
    article = soup.find("article") or soup.find(class_=lambda v: v and "article" in v.lower())
    if article:
        for p in article.find_all("p"):
            t = p.get_text(strip=True)
            if t and len(t) > 80:
                collected.append({"author": None, "text": t, "meta": {"selector": "article>p"}})
                if len(collected) >= max_items:
                    break

    # deduplicate by snippet
    seen = set()
    out = []
    for it in collected:
        key = it["text"][:160]
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out
