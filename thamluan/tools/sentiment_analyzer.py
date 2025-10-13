"""
Sentiment Analyzer Tool - Phân tích sentiment của text tiếng Việt.
Sử dụng LLM (Llama 3.1) để phân tích sentiment và opinions.
"""

import logging
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


class SentimentAnalyzerTool:
    """Tool phân tích sentiment và opinions"""

    def __init__(self):
        self.llm = ChatOllama(
            model=config.LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.3,  # Lower temperature for more consistent analysis
            num_predict=1024
        )

        self.sentiment_prompt = """Bạn là chuyên gia phân tích sentiment và ý kiến công chúng về các dự luật.

Nhiệm vụ: Phân tích sentiment và quan điểm trong đoạn text sau đây về dự luật.

Text cần phân tích:
{text}

Hãy phân tích và trả lời theo format JSON:
{{
    "sentiment": "positive/negative/neutral/mixed",
    "confidence": 0.0-1.0,
    "key_opinions": ["ý kiến 1", "ý kiến 2", ...],
    "positive_points": ["điểm tích cực 1", "điểm tích cực 2", ...],
    "negative_points": ["điểm tiêu cực 1", "điểm tiêu cực 2", ...],
    "neutral_points": ["điểm trung lập 1", "điểm trung lập 2", ...],
    "summary": "Tóm tắt ngắn gọn quan điểm chính"
}}

Lưu ý:
- sentiment: "positive" (tích cực), "negative" (tiêu cực), "neutral" (trung lập), "mixed" (lẫn lộn)
- confidence: mức độ tự tin về phân loại (0.0 đến 1.0)
- Chỉ trả về JSON, không thêm text khác"""

    def analyze_sentiment(self, text: str) -> ToolResult:
        """
        Phân tích sentiment của một đoạn text.

        Args:
            text: Text cần phân tích

        Returns:
            ToolResult với sentiment analysis
        """
        try:
            if not text or len(text.strip()) < 50:
                return ToolResult(
                    success=False,
                    error="Text quá ngắn để phân tích (cần ít nhất 50 ký tự)"
                )

            logger.info(f"Analyzing sentiment for text ({len(text)} chars)...")

            # Truncate text if too long
            max_length = 3000
            if len(text) > max_length:
                text = text[:max_length] + "..."
                logger.info(f"Text truncated to {max_length} chars")

            # Call LLM
            prompt = self.sentiment_prompt.format(text=text)
            messages = [HumanMessage(content=prompt)]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Parse JSON response
            import json
            import re

            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Fallback: basic sentiment analysis
                result = self._fallback_sentiment(text)

            logger.info(f"Sentiment: {result.get('sentiment')} (confidence: {result.get('confidence', 0):.2f})")

            return ToolResult(
                success=True,
                data=result
            )

        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            # Return fallback result
            fallback = self._fallback_sentiment(text)
            return ToolResult(
                success=True,
                data=fallback,
                metadata={'method': 'fallback', 'error': str(e)}
            )

    def _fallback_sentiment(self, text: str) -> Dict[str, Any]:
        """Fallback sentiment analysis using keywords"""
        text_lower = text.lower()

        # Vietnamese positive keywords
        positive_keywords = [
            'tốt', 'tích cực', 'ủng hộ', 'đồng ý', 'hoan nghênh', 'cần thiết',
            'quan trọng', 'hiệu quả', 'phù hợp', 'hợp lý', 'tiến bộ', 'phát triển'
        ]

        # Vietnamese negative keywords
        negative_keywords = [
            'không tốt', 'tiêu cực', 'phản đối', 'không đồng ý', 'lo ngại',
            'bất cập', 'thiếu sót', 'không phù hợp', 'không hợp lý', 'chưa rõ ràng'
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)

        if positive_count > negative_count * 1.5:
            sentiment = "positive"
            confidence = min(0.6 + positive_count * 0.05, 0.9)
        elif negative_count > positive_count * 1.5:
            sentiment = "negative"
            confidence = min(0.6 + negative_count * 0.05, 0.9)
        elif positive_count > 0 and negative_count > 0:
            sentiment = "mixed"
            confidence = 0.5
        else:
            sentiment = "neutral"
            confidence = 0.4

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "key_opinions": [],
            "positive_points": [],
            "negative_points": [],
            "neutral_points": [],
            "summary": f"Phân tích keyword: {positive_count} positive, {negative_count} negative",
            "method": "fallback"
        }

    def analyze_batch(self, texts: List[str]) -> ToolResult:
        """
        Phân tích sentiment cho nhiều texts.

        Args:
            texts: List of texts cần phân tích

        Returns:
            ToolResult với list of results
        """
        try:
            logger.info(f"Analyzing sentiment for {len(texts)} texts...")

            results = []
            for i, text in enumerate(texts, 1):
                logger.info(f"Analyzing text {i}/{len(texts)}...")
                result = self.analyze_sentiment(text)

                if result.success:
                    results.append(result.data)
                else:
                    results.append({
                        "sentiment": "unknown",
                        "confidence": 0.0,
                        "error": result.error
                    })

            # Calculate aggregate statistics
            sentiments = [r.get('sentiment') for r in results if r.get('sentiment') != 'unknown']

            sentiment_counts = {
                'positive': sentiments.count('positive'),
                'negative': sentiments.count('negative'),
                'neutral': sentiments.count('neutral'),
                'mixed': sentiments.count('mixed')
            }

            total = len(sentiments)
            sentiment_percentages = {
                k: (v / total * 100) if total > 0 else 0
                for k, v in sentiment_counts.items()
            }

            # Overall sentiment
            if sentiment_counts['positive'] > sentiment_counts['negative']:
                overall = 'positive'
            elif sentiment_counts['negative'] > sentiment_counts['positive']:
                overall = 'negative'
            else:
                overall = 'mixed'

            logger.info(f"Batch analysis complete: {sentiment_counts}")

            return ToolResult(
                success=True,
                data={
                    'results': results,
                    'count': len(results),
                    'sentiment_counts': sentiment_counts,
                    'sentiment_percentages': sentiment_percentages,
                    'overall_sentiment': overall
                }
            )

        except Exception as e:
            logger.error(f"Batch sentiment analysis error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Batch analysis failed: {str(e)}"
            )


# Singleton instance
sentiment_analyzer_tool = SentimentAnalyzerTool()