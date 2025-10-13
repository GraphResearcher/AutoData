"""
Text Analyzer Tool - Phân tích text, tạo search queries từ keywords.
"""

from typing import List, Dict, Any
import re
import logging
import json
import requests

from core.config import config
from core.types import ToolResult, ExtractedKeywords

logger = logging.getLogger(__name__)


class TextAnalyzerTool:
    """Tool để phân tích text và tạo queries"""

    def __init__(self):
        self.stopwords = config.VIETNAMESE_STOPWORDS

    def generate_search_queries(self, keywords: ExtractedKeywords, base_topic: str = "") -> ToolResult:
        """
        Tạo search queries thông minh dựa vào base_topic VÀ keywords từ PDF.

        Args:
            keywords: ExtractedKeywords object với main_keywords và key_phrases
            base_topic: Chủ đề chính (ví dụ: "Luật Khoa học Công nghệ")

        Returns:
            ToolResult với danh sách queries được tối ưu
        """
        try:
            queries = []

            # Lấy top keywords từ PDF
            top_keywords = []
            if keywords:
                # Ưu tiên key_phrases vì chứa ngữ cảnh
                top_keywords = keywords.key_phrases[:5] if keywords.key_phrases else []
                # Nếu không đủ, thêm main_keywords
                if len(top_keywords) < 3 and keywords.main_keywords:
                    top_keywords.extend(keywords.main_keywords[:3])

            # Strategy 1: Base topic với opinion keywords
            if base_topic:
                opinion_patterns = [
                    f"{base_topic} ý kiến chuyên gia",
                    f"{base_topic} phản hồi",
                    f"{base_topic} bình luận",
                    f"dư luận về {base_topic}",
                ]
                queries.extend(opinion_patterns[:3])

            # Strategy 2: Combine keywords với base topic để tìm nội dung cụ thể hơn
            if top_keywords and base_topic:
                for kw in top_keywords[:3]:
                    # Bỏ qua keywords quá ngắn hoặc không có ý nghĩa
                    if len(kw) < 5 or kw.lower() in ['nghị định', 'điều', 'khoản', 'luật']:
                        continue
                    queries.append(f"{base_topic} {kw}")

            # Strategy 3: Nếu không có keywords, dùng các pattern chung
            if not queries:
                queries.extend([
                    f"{base_topic} ý kiến người dân",
                    f"{base_topic} thảo luận",
                    f"phản hồi về {base_topic}",
                ])

            # Xóa trùng lặp và clean up
            unique_queries = []
            seen = set()
            for q in queries:
                q_clean = q.strip().lower()
                if q_clean not in seen and len(q) > 10:
                    unique_queries.append(q)
                    seen.add(q_clean)

            # Limit to reasonable number
            final_queries = unique_queries[:8]

            logger.info(f"Generated {len(final_queries)} optimized search queries")
            logger.info(f"Sample queries: {final_queries[:3]}")

            return ToolResult(
                success=True,
                data={
                    'queries': final_queries,
                    'count': len(final_queries),
                    'keywords_used': top_keywords
                }
            )

        except Exception as e:
            logger.error(f"Query generation error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to generate queries: {str(e)}"
            )

    def create_query_variations(self, base_query: str) -> List[str]:
        """
        Tạo các biến thể của query.

        Args:
            base_query: Query gốc

        Returns:
            Danh sách query variations
        """
        variations = [base_query]

        # Add Vietnamese opinion keywords
        opinion_keywords = [
            "ý kiến",
            "bình luận",
            "phản hồi",
            "thảo luận",
            "đóng góp",
            "nhận xét",
            "góp ý"
        ]

        for keyword in opinion_keywords:
            variations.append(f"{base_query} {keyword}")

        return variations[:5]

    def extract_entities(self, text: str) -> ToolResult:
        """
        Extract entities từ text (đơn giản).
        Có thể improve bằng NER models sau.

        Args:
            text: Text cần extract

        Returns:
            ToolResult với entities
        """
        try:
            # Pattern cho các entities phổ biến
            patterns = {
                'dates': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                'numbers': r'\d+(?:\.\d+)?%?',
                'organizations': r'(?:Bộ|Cục|Vụ|Sở|Ban|Ủy ban)\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]\w+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]\w+)*',
                'laws': r'Luật\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]\w+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]\w+)*'
            }

            entities = {}
            for entity_type, pattern in patterns.items():
                matches = re.findall(pattern, text)
                entities[entity_type] = list(set(matches))[:10]  # Unique và limit

            logger.info(f"Extracted entities: {sum(len(v) for v in entities.values())} total")

            return ToolResult(
                success=True,
                data=entities
            )

        except Exception as e:
            logger.error(f"Entity extraction error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to extract entities: {str(e)}"
            )

    def summarize_text(self, text: str, max_length: int = 500) -> ToolResult:
        """
        Tạo summary đơn giản của text (extractive).

        Args:
            text: Text cần summarize
            max_length: Độ dài tối đa của summary

        Returns:
            ToolResult với summary
        """
        try:
            if len(text) <= max_length:
                return ToolResult(
                    success=True,
                    data={'summary': text, 'length': len(text)}
                )

            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

            # Take first N sentences
            summary_sentences = []
            current_length = 0

            for sentence in sentences:
                if current_length + len(sentence) <= max_length:
                    summary_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break

            summary = '. '.join(summary_sentences) + '.'

            logger.info(f"Created summary: {len(summary)} chars from {len(text)} chars")

            return ToolResult(
                success=True,
                data={
                    'summary': summary,
                    'length': len(summary),
                    'original_length': len(text)
                }
            )

        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to summarize: {str(e)}"
            )

    def clean_text(self, text: str) -> str:
        """
        Clean text (remove extra spaces, special chars).

        Args:
            text: Text cần clean

        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters (giữ Vietnamese)
        text = re.sub(r'[^\w\s\u00C0-\u1EF9.,;:!?()-]', '', text)

        return text.strip()

    def calculate_text_stats(self, text: str) -> ToolResult:
        """
        Tính toán statistics của text.

        Args:
            text: Text cần analyze

        Returns:
            ToolResult với stats
        """
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)

            stats = {
                'char_count': len(text),
                'word_count': len(words),
                'sentence_count': len([s for s in sentences if s.strip()]),
                'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
                'avg_sentence_length': len(words) / len(sentences) if sentences else 0
            }

            return ToolResult(
                success=True,
                data=stats
            )

        except Exception as e:
            logger.error(f"Stats calculation error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to calculate stats: {str(e)}"
            )

    def analyze_relevance(self, articles: List[Dict[str, Any]], topic: str = "") -> ToolResult:
        """
        Lọc bài báo theo độ liên quan đến topic sử dụng mô hình LLaMA qua Ollama API.

        Args:
            articles: Danh sách bài báo [{'title':..., 'content':...}, ...]
            topic: Chủ đề để đánh giá độ liên quan (ví dụ: "Luật Khoa học Công nghệ")

        Returns:
            ToolResult chứa các bài báo được giữ lại (relevant)
        """
        try:
            if not articles:
                return ToolResult(success=False, error="No articles provided")

            filtered = []

            for i, art in enumerate(articles, 1):
                title = art.get('title', '')
                content = art.get('content', '')[:2000]

                prompt = f"""
                Bạn là chuyên gia phân tích thông tin.
                Chủ đề quan tâm: "{topic}".
                ---
                Tiêu đề: {title}
                Nội dung: {content}
                ---
                Nhiệm vụ:
                - Đánh giá xem bài viết có liên quan đến chủ đề trên không.
                - Nếu có liên quan và chứa ý kiến, phản hồi, hoặc phân tích hữu ích → trả lời "KEEP".
                - Nếu không liên quan, tin rác, hoặc chỉ sao chép thông cáo → trả lời "DROP".
                Chỉ trả về duy nhất một từ: KEEP hoặc DROP.
                """

                payload = {
                    "model": config.LLM_MODEL,
                    "prompt": prompt,
                    "temperature": 0.2,
                }

                response = requests.post(
                    f"{config.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=45
                )

                if response.status_code == 200:
                    output = ""
                    for line in response.text.strip().splitlines():
                        try:
                            data = json.loads(line)
                            output += data.get("response", "")
                        except Exception:
                            pass

                    decision = output.strip().upper()
                    logger.info(f"[{i}/{len(articles)}] {title[:40]}... → {decision}")

                    if "KEEP" in decision:
                        filtered.append(art)

                else:
                    logger.warning(f"⚠️ Ollama request failed ({response.status_code}) for article: {title}")

            logger.info(f"✅ AI filtering done: {len(filtered)}/{len(articles)} relevant articles")

            # Save filtered articles (optional)
            try:
                with open("filtered_articles.json", "w", encoding="utf-8") as f:
                    json.dump(filtered, f, ensure_ascii=False, indent=2)
            except Exception as save_err:
                logger.warning(f"Could not save filtered results: {save_err}")

            return ToolResult(success=True, data={"filtered": filtered, "count": len(filtered)})

        except Exception as e:
            logger.error(f"AI filtering error: {str(e)}")
            return ToolResult(success=False, error=f"AI filtering failed: {str(e)}")
# Singleton instance
text_analyzer_tool = TextAnalyzerTool()