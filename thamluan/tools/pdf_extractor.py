"""
PDF Extractor Tool - Trích xuất text và keywords từ PDF.
"""

import PyPDF2
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any
import re
import logging

from core.config import config
from core.types import ToolResult, ExtractedKeywords

logger = logging.getLogger(__name__)


class PDFExtractorTool:
    """Tool để extract content từ PDF files"""

    def __init__(self):
        self.min_keyword_length = config.MIN_KEYWORD_LENGTH
        self.max_keywords = config.MAX_KEYWORDS
        self.stopwords = config.VIETNAMESE_STOPWORDS

    def extract_text(self, pdf_path: str, method: str = "pdfplumber") -> ToolResult:
        """
        Extract toàn bộ text từ PDF.

        Args:
            pdf_path: Đường dẫn đến PDF file
            method: "pdfplumber" hoặc "pypdf2"

        Returns:
            ToolResult với text content
        """
        try:
            path = Path(pdf_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"PDF file not found: {pdf_path}"
                )

            logger.info(f"Extracting text from {path.name} using {method}")

            if method == "pdfplumber":
                text = self._extract_with_pdfplumber(path)
            else:
                text = self._extract_with_pypdf2(path)

            # Clean text
            text = self._clean_text(text)

            logger.info(f"Extracted {len(text)} characters from {path.name}")

            return ToolResult(
                success=True,
                data={
                    'text': text,
                    'length': len(text),
                    'word_count': len(text.split()),
                    'method': method
                }
            )

        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to extract text: {str(e)}"
            )

    def _extract_with_pdfplumber(self, path: Path) -> str:
        """Extract text using pdfplumber (tốt hơn cho Vietnamese)"""
        text_parts = []

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return '\n\n'.join(text_parts)

    def _extract_with_pypdf2(self, path: Path) -> str:
        """Extract text using PyPDF2 (fallback)"""
        text_parts = []

        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return '\n\n'.join(text_parts)

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters (giữ lại Vietnamese)
        text = re.sub(r'[^\w\s\u00C0-\u1EF9.,;:!?()-]', '', text)
        return text.strip()

    def extract_keywords(self, text: str, max_keywords: int = None) -> ToolResult:
        """
        Extract keywords từ text.
        Sử dụng frequency-based extraction đơn giản.

        Args:
            text: Text cần extract keywords
            max_keywords: Số lượng keywords tối đa

        Returns:
            ToolResult với danh sách keywords
        """
        try:
            if max_keywords is None:
                max_keywords = self.max_keywords

            # Tokenize (đơn giản)
            words = re.findall(r'\b\w+\b', text.lower())

            # Filter stopwords và short words
            filtered_words = [
                w for w in words
                if len(w) >= self.min_keyword_length and w not in self.stopwords
            ]

            # Count frequency
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # Sort by frequency
            sorted_words = sorted(
                word_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Get top keywords
            keywords = [word for word, freq in sorted_words[:max_keywords] if freq >= config.MIN_KEYWORD_FREQUENCY]

            logger.info(f"Extracted {len(keywords)} keywords")

            return ToolResult(
                success=True,
                data={
                    'keywords': keywords,
                    'count': len(keywords),
                    'word_frequencies': dict(sorted_words[:max_keywords])
                }
            )

        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to extract keywords: {str(e)}"
            )

    def extract_key_phrases(self, text: str, max_phrases: int = 20) -> ToolResult:
        """
        Extract key phrases (2-3 từ liên tiếp).

        Args:
            text: Text cần extract
            max_phrases: Số lượng phrases tối đa

        Returns:
            ToolResult với danh sách key phrases
        """
        try:
            # Extract bigrams và trigrams
            words = re.findall(r'\b\w+\b', text.lower())

            phrases = []
            phrase_freq = {}

            # Bigrams
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i + 1]}"
                if all(len(w) >= 3 and w not in self.stopwords for w in [words[i], words[i + 1]]):
                    phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1

            # Trigrams
            for i in range(len(words) - 2):
                phrase = f"{words[i]} {words[i + 1]} {words[i + 2]}"
                if all(len(w) >= 3 and w not in self.stopwords for w in [words[i], words[i + 1], words[i + 2]]):
                    phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1

            # Sort by frequency
            sorted_phrases = sorted(
                phrase_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )

            key_phrases = [phrase for phrase, freq in sorted_phrases[:max_phrases] if freq >= 2]

            logger.info(f"Extracted {len(key_phrases)} key phrases")

            return ToolResult(
                success=True,
                data={
                    'key_phrases': key_phrases,
                    'count': len(key_phrases)
                }
            )

        except Exception as e:
            logger.error(f"Error extracting phrases: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to extract phrases: {str(e)}"
            )

    def extract_all(self, pdf_path: str) -> ToolResult:
        """
        Extract tất cả: text, keywords, key phrases.

        Args:
            pdf_path: Đường dẫn đến PDF

        Returns:
            ToolResult với ExtractedKeywords object
        """
        try:
            # Extract text
            text_result = self.extract_text(pdf_path)
            if not text_result.success:
                return text_result

            text = text_result.data['text']

            # Extract keywords
            keywords_result = self.extract_keywords(text)
            keywords = keywords_result.data['keywords'] if keywords_result.success else []

            # Extract key phrases
            phrases_result = self.extract_key_phrases(text)
            key_phrases = phrases_result.data['key_phrases'] if phrases_result.success else []

            # Create summary (first 500 chars)
            summary = text[:500] + "..." if len(text) > 500 else text

            extracted = ExtractedKeywords(
                main_keywords=keywords[:20],
                entities=[],  # Có thể thêm NER sau
                key_phrases=key_phrases,
                summary=summary
            )

            logger.info(f"Extracted all content from {Path(pdf_path).name}")

            return ToolResult(
                success=True,
                data={
                    'extracted_keywords': extracted,
                    'full_text': text,
                    'text_length': len(text)
                }
            )

        except Exception as e:
            logger.error(f"Error in extract_all: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to extract all content: {str(e)}"
            )


# Singleton instance
pdf_extractor_tool = PDFExtractorTool()