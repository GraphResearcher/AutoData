"""
autodata.tools.legal
Utilities to parse Vietnamese legal documents: split into Điều/Khoản/Mục/Chương,
and extract numbered clauses or defined-term sections.
"""
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Patterns tuned for Vietnamese legal texts
_RE_ARTICLE = re.compile(r"(^|\n)(Điều)\s+(\d+)[\.\s]", flags=re.MULTILINE | re.IGNORECASE)
_RE_SECTION = re.compile(r"(^|\n)(Chương|Mục|Phần)\s+[IVXLC\d]+", flags=re.MULTILINE | re.IGNORECASE)
_RE_CLAUSE = re.compile(r"(Khoản|Điểm)\s+(\d+[\w\-]*)", flags=re.IGNORECASE)

def split_into_articles(text: str) -> List[Dict]:
    """
    Split text into articles (Điều <n>) if present.
    Returns list of dicts: {'article_no': n, 'title': title_line, 'content': '...'}.
    Falls back to returning one element with whole text if pattern not found.
    """
    if not text or len(text) < 50:
        return []

    # find all article starts
    starts = [m for m in _RE_ARTICLE.finditer(text)]
    if not starts:
        # fallback: try split on 'Điều' anywhere
        parts = re.split(r"(?m)^\s*Điều\s+\d+", text)
        if len(parts) <= 1:
            return [{"article_no": None, "title": None, "content": text.strip()}]
    articles = []
    # collect boundaries
    indices = [m.start() for m in starts]
    indices.append(len(text))
    for i, m in enumerate(starts):
        start_idx = m.start()
        # article number
        num = m.group(3)
        title_line = text[m.start(): text.find("\n", m.start())].strip()
        end_idx = indices[i+1]
        content = text[m.end():end_idx].strip()
        articles.append({"article_no": int(num) if num and num.isdigit() else num, "title": title_line, "content": content})
    if not articles:
        return [{"article_no": None, "title": None, "content": text.strip()}]
    return articles

def extract_clauses_from_article(article_text: str) -> List[Dict]:
    """
    From an article content, attempt to split into clauses (Khoản, Điểm).
    Returns list of {'clause_type':'Khoản'/'Điểm','no':..., 'text':...}
    """
    clauses = []
    # split at "Khoản <n>" occurrences
    parts = re.split(r"(?i)(?=\bKhoản\s+\d+)", article_text)
    if len(parts) == 1:
        # fallback split at "Điểm" maybe
        parts2 = re.split(r"(?i)(?=\bĐiểm\s+[a-z0-9\)\(]+)", article_text)
        parts = parts2 if len(parts2) > 1 else parts

    for p in parts:
        m = re.match(r"(?i)\s*(Khoản|Điểm)\s*([^\s\.\)\:]+)", p)
        if m:
            typ = m.group(1)
            no = m.group(2)
            content = p[m.end():].strip()
            clauses.append({"clause_type": typ, "no": no, "text": content})
        else:
            # if first segment without label, attach as preface
            if clauses:
                clauses[-1]["text"] = clauses[-1]["text"] + "\n" + p.strip()
            else:
                clauses.append({"clause_type": None, "no": None, "text": p.strip()})
    return clauses
