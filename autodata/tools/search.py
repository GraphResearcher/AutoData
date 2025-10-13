"""
autodata.tools.search
Search utilities. If GOOGLE_API_KEY and GOOGLE_CSE_ID present, use Google Custom Search API.
Otherwise return empty list (caller can fallback to site-scan).
"""
import os
import logging
from typing import List, Dict

import requests

logger = logging.getLogger(__name__)


def search_discussions(query: str, num: int = 10) -> List[Dict]:
    """
    Use Google Custom Search API (if configured) to search web for discussions/articles.
    Returns list of dicts: {'title':..., 'link':..., 'snippet':...}
    """
    google_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CSE_ID")
    out = []

    if not google_key or not google_cx:
        logger.warning("search_discussions: GOOGLE_API_KEY/GOOGLE_CSE_ID not configured.")
        return out

    try:
        params = {"key": google_key, "cx": google_cx, "q": query, "num": min(10, num)}
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            out.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
            })
    except Exception as e:
        logger.warning("search_discussions: Google CSE error: %s", e)
    return out
