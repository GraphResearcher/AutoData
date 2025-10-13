"""
autodata.tools.keywords
Keyword/keyphrase extraction tuned for Vietnamese legal texts.
Uses underthesea for tokenization if available; TF-IDF n-grams as main method.
"""
import logging
import re
from typing import List, Optional, Set

logger = logging.getLogger(__name__)

# optional Vietnamese tokenizer
try:
    from underthesea import word_tokenize, sent_tokenize
except Exception:
    word_tokenize = None
    sent_tokenize = None

# sklearn import inside function to avoid import error if not installed
DEFAULT_VI_STOPWORDS: Set[str] = {
    "và", "của", "là", "các", "có", "cho", "được", "trong",
    "với", "những", "một", "khi", "tại", "theo", "để", "vì", "này",
    "bằng", "hoặc", "như", "nên", "đã", "đang", "sẽ", "cần"
}


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[^\w\s\u00C0-\u024F\u0100-\u024F]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenize_vi(text: str) -> List[str]:
    if not text:
        return []
    if word_tokenize:
        try:
            tok_text = word_tokenize(text, format="text")
            return [t for t in tok_text.split() if t]
        except Exception:
            pass
    cleaned = re.sub(r"[^\w\s\u00C0-\u024F]", " ", text)
    return [t for t in re.split(r"\s+", cleaned.lower()) if t]


def extract_keywords(text: str, top_n: int = 10, ngram_range=(1, 3), stopwords: Optional[Set[str]] = None) -> List[str]:
    """
    Extract top_n keywords or keyphrases from Vietnamese text using TF-IDF.
    Returns list of phrases (strings).
    """
    if not text or len(text) < 40:
        return []

    if stopwords is None:
        stopwords = DEFAULT_VI_STOPWORDS

    # create pseudo-documents by paragraphs or sentences
    docs = []
    if sent_tokenize:
        try:
            sents = sent_tokenize(text)
            # group sentences into chunks of ~5
            chunk = []
            chunks = []
            for s in sents:
                chunk.append(s)
                if len(chunk) >= 5:
                    chunks.append(" ".join(chunk))
                    chunk = []
            if chunk:
                chunks.append(" ".join(chunk))
            docs = chunks or [text]
        except Exception:
            docs = [text]
    else:
        docs = [p for p in text.split("\n\n") if len(p.strip()) > 50]
        if not docs:
            docs = [text]

    tokenized_docs = []
    for d in docs:
        toks = _tokenize_vi(d)
        toks = [t for t in toks if t not in stopwords and len(t) > 1]
        tokenized_docs.append(" ".join(toks))

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vect = TfidfVectorizer(ngram_range=ngram_range, max_df=0.9, min_df=1)
        X = vect.fit_transform(tokenized_docs)
        scores = X.sum(axis=0).A1
        terms = vect.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
        keywords = [t.replace("_", " ") for t, _ in ranked[:top_n]]
        return keywords
    except Exception as e:
        logger.warning("extract_keywords: TF-IDF failed: %s", e)
        # fallback frequency-based
        tokens = _tokenize_vi(_clean_text(text))
        freq = {}
        for w in tokens:
            if w in stopwords or len(w) < 2:
                continue
            freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [w for w, _ in top]
