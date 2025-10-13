"""
autodata.tools.web
Helpers for HTTP requests, URL normalization and HTML parsing (find PDF links).
"""
import os
import logging
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {"User-Agent": os.getenv("AUTODATA_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")}


def safe_request(url: str, timeout: int = 15) -> Optional[requests.Response]:
    """Make a GET request with basic headers and error handling."""
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning("safe_request: failed to fetch %s: %s", url, e)
        return None


def get_page_content(url: str, timeout: int = 15) -> Optional[str]:
    """Return HTML text for a URL (None on error)."""
    r = safe_request(url, timeout=timeout)
    if r is None:
        return None
    return r.text


def normalize_url(base: str, href: str) -> str:
    """Convert relative href to absolute URL using base."""
    try:
        return urljoin(base, href)
    except Exception:
        return href


def find_pdf_links(html: str, base_url: str) -> List[str]:
    """
    Parse HTML and return absolute links that look like PDFs.
    Heuristics:
      - href endswith .pdf
      - anchor type contains 'pdf'
      - anchor text contains 'pdf' or 'tải về', 'tải xuống'
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = normalize_url(base_url, href)
        href_l = href.lower()
        text = (a.get_text() or "").lower()
        # direct pdf extension
        if href_l.endswith(".pdf"):
            links.append(full)
            continue
        # type attribute
        t = (a.get("type") or "").lower()
        if "pdf" in t:
            links.append(full)
            continue
        # anchor text hints
        if "pdf" in text or "tải" in text or "tải về" in text or "tải xuống" in text:
            links.append(full)
            continue

    # remove duplicates, preserve order
    seen = set()
    out = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out
