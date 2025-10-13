"""
autodata.tools.pdf
Robust PDF download & text extraction for Vietnamese documents.
Primary: pdfplumber; fallback: PyMuPDF (fitz); optional OCR with pdf2image+pytesseract.
"""
import io
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)

# optional libraries
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# OCR optional
try:
    from pdf2image import convert_from_bytes
    import pytesseract
except Exception:
    convert_from_bytes = None
    pytesseract = None

import requests
import os


def download_pdf_bytes(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download a PDF and return raw bytes (None on failure)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoDataBot/1.0)"}
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            return r.content
    except Exception as e:
        logger.error("download_pdf_bytes: failed to download %s: %s", url, e)
        return None


def save_pdf_bytes(content: bytes, dest_path: str) -> str:
    """Save bytes to dest_path (create dirs) and return path."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(content)
    return dest_path


def _try_pdfplumber(data: Union[str, bytes]) -> str:
    try:
        if pdfplumber is None:
            return ""
        if isinstance(data, (bytes, bytearray)):
            fp = io.BytesIO(data)
            with pdfplumber.open(fp) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
        else:
            with pdfplumber.open(data) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n\n".join([p for p in pages if p])
    except Exception as e:
        logger.debug("pdfplumber failed: %s", e)
        return ""


def _try_pymupdf(data: Union[str, bytes]) -> str:
    try:
        if fitz is None:
            return ""
        if isinstance(data, (bytes, bytearray)):
            doc = fitz.open(stream=data, filetype="pdf")
        else:
            doc = fitz.open(data)
        pages = []
        for p in doc:
            pages.append(p.get_text("text") or "")
        doc.close()
        return "\n\n".join([p for p in pages if p])
    except Exception as e:
        logger.debug("PyMuPDF failed: %s", e)
        return ""


def _try_ocr_bytes(data: bytes) -> str:
    if convert_from_bytes is None or pytesseract is None:
        logger.debug("OCR libs not available.")
        return ""
    try:
        images = convert_from_bytes(data)
        texts = []
        for img in images:
            txt = pytesseract.image_to_string(img, lang="vie+eng")
            texts.append(txt)
        return "\n\n".join([t for t in texts if t.strip()])
    except Exception as e:
        logger.debug("OCR failed: %s", e)
        return ""


def extract_text_from_pdf(path_or_bytes: Union[str, bytes], ocr_enable: bool = False) -> str:
    """
    Extract text from a PDF (path or raw bytes).
    Strategy:
      1) Try pdfplumber
      2) If too short, try PyMuPDF
      3) If still short and ocr_enable True and bytes available -> OCR
    Returns concatenated text.
    """
    text = _try_pdfplumber(path_or_bytes)
    if text and len(text) > 120:
        return text

    text2 = _try_pymupdf(path_or_bytes)
    if text2 and len(text2) > len(text):
        text = text2

    # OCR fallback if requested and we have bytes
    if (not text or len(text) < 200) and ocr_enable and isinstance(path_or_bytes, (bytes, bytearray)):
        try:
            ocr_text = _try_ocr_bytes(path_or_bytes)
            if ocr_text and len(ocr_text) > len(text):
                text = ocr_text
        except Exception as e:
            logger.debug("OCR attempt failed: %s", e)

    return (text or "").strip()
