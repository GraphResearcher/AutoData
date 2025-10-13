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
        Tạo search queries chỉ dựa vào base_topic, bỏ key_phrases.

        Args:
            keywords: ExtractedKeywords object (bỏ qua trong phiên bản này)
            base_topic: Chủ đề chính (ví dụ: "Luật Khoa học Công nghệ")

        Returns:
            ToolResult với danh sách queries
        """
        try:
            queries = []

            if base_topic:
                # Mẫu truy vấn phổ biến cho việc thu thập ý kiến công chúng
                queries.extend([
                    f"{base_topic} ý kiến người dân",
                    f"{base_topic} bình luận",
                    f"{base_topic} thảo luận",
                    f"phản hồi về {base_topic}",
                    f"đánh giá {base_topic}",
                    f"góp ý {base_topic}",
                    f"người dân nói gì về {base_topic}",
                    f"quan điểm công chúng {base_topic}",
                    f"{base_topic} dư luận xã hội",
                    f"{base_topic} trên mạng xã hội",
                ])

            # Xóa trùng lặp và giới hạn kết quả
            unique_queries = list(dict.fromkeys(queries))
            final_queries = unique_queries[:5]

            logger.info(f"Generated {len(final_queries)} base-topic search queries")

            return ToolResult(
                success=True,
                data={
                    'queries': final_queries,
                    'count': len(final_queries)
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