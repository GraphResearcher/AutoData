import logging
from typing import Dict, Any, List
import uuid
import numpy as np
from textblob import TextBlob
from datetime import datetime

from agents.base import BaseAgent
from core.types import AgentState, AgentRole, TaskType
from tools import search_engine_tool, text_analyzer_tool, csv_exporter_tool, vector_db_tool

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """Search Agent - Tìm kiếm thông tin về opinions trên web."""

    def __init__(self):
        super().__init__(
            role=AgentRole.SEARCH_AGENT,
            name="Search Agent",
            description="Searches for opinions and discussions on the web"
        )

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"🔍 {self.name} executing...")

            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.SEARCH_OPINIONS:
                return state

            extracted_keywords = state.get('extracted_keywords')
            if not extracted_keywords:
                error_msg = "No keywords found in state"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)

            project_name = state['project_name']
            query_result = text_analyzer_tool.generate_search_queries(
                extracted_keywords,
                base_topic=project_name
            )

            if not query_result.success:
                task = self.complete_task(current_task, {}, error=query_result.error)
                return self.log_error(state, query_result.error)

            search_queries = query_result.data['queries'][:10]
            search_results = []

            # Search ONLY on Vietnamese trusted news sites (no Google)
            # Faster and more reliable than Google search
            logger.info("🔍 Searching directly on Vietnamese trusted news sites...")
            try:
                from tools.direct_news_search import direct_news_search_tool

                # Use multiple queries for better coverage
                for idx, query in enumerate(search_queries[:5], 1):
                    logger.info(f"📰 Query {idx}/5: '{query}'")
                    result = direct_news_search_tool.search_all_sites(
                        query,
                        max_results_per_site=5  # Get more results from each site
                    )
                    if result.success:
                        new_results = result.data['results']
                        search_results.extend(new_results)
                        logger.info(f"  → Found {len(new_results)} new articles")

                    # Stop if we already have plenty of results
                    if len(search_results) >= 30:
                        logger.info(f"✅ Got enough results ({len(search_results)}), stopping search")
                        break

                logger.info(f"📊 Total found: {len(search_results)} articles from Vietnamese news sites")
            except Exception as e:
                logger.warning(f"Direct news search failed: {str(e)}")

            # If we still have no results, that's an error
            if not search_results:
                error_msg = "No search results found from any source"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)

            # Step 1: URL validation and de-duplication
            unique_results = []
            seen_urls = set()
            for result in search_results:
                url = result.get('url', '')
                # Skip invalid URLs
                if not url or not (url.startswith('http://') or url.startswith('https://')):
                    continue
                # Skip duplicates
                if url in seen_urls:
                    continue
                # Skip homepage-only URLs (likely false positives)
                if url.endswith('/') or url.count('/') <= 3:
                    # Allow if it has article indicators in the path
                    if not any(indicator in url.lower() for indicator in
                               ['-', 'tin-tuc', 'bai-viet', 'news', 'article', '.htm']):
                        continue

                seen_urls.add(url)
                unique_results.append(result)

            logger.info(f"📊 After validation: {len(unique_results)} unique valid URLs")

            # Step 2: Keyword matching score for better relevance
            important_keywords = []
            if extracted_keywords:
                important_keywords = (extracted_keywords.key_phrases[:5] if extracted_keywords.key_phrases else []) + \
                                     (extracted_keywords.main_keywords[:5] if extracted_keywords.main_keywords else [])
                important_keywords = [kw.lower() for kw in important_keywords if len(kw) > 3]

            def calculate_relevance_score(result):
                """Calculate relevance based on keyword matching"""
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                combined_text = title + ' ' + snippet

                score = 0
                # Title matches worth more
                for kw in important_keywords:
                    if kw in title:
                        score += 3
                    elif kw in snippet:
                        score += 1

                # Bonus for opinion indicators
                opinion_words = ['ý kiến', 'bình luận', 'phản hồi', 'góp ý', 'thảo luận', 'tranh luận', 'chuyên gia']
                for word in opinion_words:
                    if word in combined_text:
                        score += 2
                        break

                return score

            # Score all results
            for result in unique_results:
                result['relevance_score'] = calculate_relevance_score(result)

            # Step 3: Prioritize trusted domains + high scores
            from core.config import config
            trusted_results = [r for r in unique_results if any(d in r['url'] for d in config.TRUSTED_DOMAINS)]
            other_results = [r for r in unique_results if not any(d in r['url'] for d in config.TRUSTED_DOMAINS)]

            # Sort both by relevance score
            trusted_results = sorted(trusted_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
            other_results = sorted(other_results, key=lambda x: x.get('relevance_score', 0), reverse=True)

            # Combine: trusted first, then high-scoring others
            final_results = trusted_results[:25] + other_results[:10]  # Total max 35

            avg_score = sum(r.get('relevance_score', 0) for r in final_results) / len(
                final_results) if final_results else 0
            logger.info(
                f"📊 Final selection: {len(trusted_results[:25])} trusted, {len(other_results[:10])} other sources")
            logger.info(f"📊 Average relevance score: {avg_score:.1f}")

            task = self.complete_task(current_task, {
                'search_queries': search_queries,
                'total_results': len(search_results),
                'unique_results': len(unique_results),
                'final_results': len(final_results),
                'avg_relevance': avg_score
            })

            state = self.update_state(state, {
                'current_task': task,
                'search_queries': search_queries,
                'search_results': final_results
            })

            return state

        except Exception as e:
            logger.error(f"Search agent error: {str(e)}")
            return self.log_error(state, f"Search failed: {str(e)}")


class ArticleAnalyzerAgent(BaseAgent):
    """Article Analyzer Agent - Scrape và phân tích sentiment với hạn chế loop."""

    MAX_LOOP = 5  # Giới hạn vòng lặp

    def __init__(self):
        super().__init__(
            role=AgentRole.SCRAPER_AGENT,
            name="Article Analyzer Agent",
            description="Scrapes articles and analyzes sentiment of public opinions"
        )

    def analyze_sentiment(self, text: str) -> str:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        return "neutral"

    async def execute(self, state: AgentState) -> AgentState:
        try:
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.SCRAPE_ARTICLES:
                return state

            # Use state-based loop counter instead of instance variable
            scrape_loop_count = state.get('scrape_loop_count', 0)

            # Check if max loop reached
            if scrape_loop_count >= self.MAX_LOOP:
                logger.warning(f"Max loop reached for {self.name} (count: {scrape_loop_count})")
                # Complete the task and mark scrape as done
                task = self.complete_task(current_task, {
                    'articles_count': 0,
                    'urls_scraped': 0,
                    'max_loop_reached': True,
                    'articles': []
                })
                state = self.update_state(state, {
                    'current_task': task,
                    'scrape_articles_done': True
                })
                return state

            urls_to_scrape = current_task.input_data.get('urls_to_scrape', [])
            if not urls_to_scrape:
                # No URLs to scrape, mark as done
                task = self.complete_task(current_task, {
                    'articles_count': 0,
                    'urls_scraped': 0,
                    'articles': []
                })
                state = self.update_state(state, {
                    'current_task': task,
                    'scrape_articles_done': True
                })
                return state

            from tools.article_scraper import article_scraper_tool
            existing_urls = state.get('processed_urls', set())
            scrape_result = article_scraper_tool.scrape_multiple_articles(urls_to_scrape, existing_urls=existing_urls)

            if scrape_result.success:
                articles = scrape_result.data['articles']
                scraped_urls = [a.url for a in articles]

                # Analyze sentiment for each article
                analyzed_articles = state.get('analyzed_articles', [])
                analyzed_articles_new = []
                for a in articles:
                    a_dict = a.to_dict()
                    a_dict['sentiment'] = self.analyze_sentiment(a_dict.get('content', ''))
                    analyzed_articles_new.append(a_dict)
                    analyzed_articles.append(a_dict)

                task = self.complete_task(current_task, {
                    'articles_count': len(articles),
                    'urls_scraped': len(scraped_urls),
                    'articles': analyzed_articles_new  # Pass articles in output_data
                })

                # Update state with all changes at once
                state = self.update_state(state, {
                    'current_task': task,
                    'processed_urls': existing_urls.union(scraped_urls),
                    'analyzed_articles': analyzed_articles,
                    'scrape_articles_done': True
                })

                logger.info(f"✅ Analyzed {len(analyzed_articles_new)} articles with sentiment")
                logger.info(f"📊 Total analyzed articles in state: {len(analyzed_articles)}")
            else:
                task = self.complete_task(current_task, {}, error=scrape_result.error)
                # Still mark as done even on error to prevent infinite loop
                state = self.update_state(state, {
                    'current_task': task,
                    'scrape_articles_done': True
                })
                state = self.log_error(state, scrape_result.error)

            # Increment state-based loop counter
            state['scrape_loop_count'] = scrape_loop_count + 1
            return state

        except Exception as e:
            logger.error(f"Article analyzer error: {str(e)}")
            current_task = state.get('current_task')
            if current_task:
                task = self.complete_task(current_task, {}, error=f"Article analysis failed: {str(e)}")
                state = self.update_state(state, {
                    'current_task': task,
                    'scrape_articles_done': True,
                    'scrape_loop_count': state.get('scrape_loop_count', 0) + 1
                })
            return self.log_error(state, f"Article analysis failed: {str(e)}")

class ExporterAgent(BaseAgent):
    """Exporter Agent - Xuất bài báo ra CSV và lưu vào VectorDB, tránh trùng vector."""

    MAX_LOOP = 3

    def __init__(self, embedding_model=None):
        super().__init__(
            role=AgentRole.SCRAPER_AGENT,
            name="Exporter Agent",
            description="Exports articles to CSV and vector database"
        )
        self.embedding_model = embedding_model  # Có thể truyền từ ngoài hoặc khởi tạo bên trong

    async def execute(self, state: AgentState) -> AgentState:
        try:
            # Use state-based loop counter
            export_loop_count = state.get('export_loop_count', 0)

            if export_loop_count >= self.MAX_LOOP:
                logger.warning(f"Max loop reached for {self.name} (count: {export_loop_count})")
                return state

            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.EXPORT_DATA:
                return state

            articles = state.get('analyzed_articles', [])
            logger.info(f"📊 ExporterAgent found {len(articles)} articles in state")
            if not articles:
                task = self.complete_task(current_task, {}, error="No articles found to export")
                state = self.update_state(state, {'current_task': task, 'is_complete': True})
                return self.log_error(state, "No articles found to export")

            # Export CSV
            project_name = state['project_name'].replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{project_name}_articles_{timestamp}.csv"

            export_result = csv_exporter_tool.export_dict_list(articles, filename)
            if not export_result.success:
                task = self.complete_task(current_task, {}, error=export_result.error)
                state = self.update_state(state, {'current_task': task, 'is_complete': True})
                return self.log_error(state, export_result.error)
            csv_path = export_result.data['filepath']
            logger.info(f"✅ Exported {len(articles)} articles to {csv_path}")

            # Khởi tạo embedding model nếu chưa có
            if self.embedding_model is None:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

            # Tạo embeddings cho bài báo
            article_texts = [a.get('content', '') for a in articles if a.get('content')]

            if article_texts:
                logger.info(f"Generating embeddings for {len(article_texts)} articles...")
                embeddings = self.embedding_model.encode(article_texts, convert_to_numpy=True)

                # Chuẩn bị metadata và id
                metadatas = [
                    {
                        'title': a.get('title', 'Untitled'),
                        'url': a.get('url', ''),
                        'sentiment': a.get('sentiment', 'neutral'),
                        'source': a.get('source', ''),
                        'type': 'article'
                    }
                    for a in articles if a.get('content')
                ]
                ids = [f"article_{uuid.uuid4().hex}" for _ in article_texts]

                # Lưu vào Vector DB nếu collection tồn tại
                collection_name = state.get('vector_db_collection')
                if collection_name:
                    logger.info(f"Adding {len(article_texts)} articles to Vector DB collection: {collection_name}")
                    result = vector_db_tool.add_documents(
                        collection_name=collection_name,
                        documents=article_texts,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=ids,
                        similarity_threshold=0.95  # tránh trùng vector
                    )
                    if result.success:
                        logger.info(f"✅ Successfully added articles to Vector DB")
                    else:
                        logger.error(f"VectorDB error: {result.error}")
            else:
                logger.warning("No article content found to add to Vector DB")

            # Cập nhật state
            task = self.complete_task(current_task, {
                'csv_path': csv_path,
                'articles_count': len(articles),
                'file_size': export_result.data['file_size']
            })
            state = self.update_state(state, {
                'current_task': task,
                'csv_output_path': csv_path,
                'is_complete': True,
                'export_loop_count': export_loop_count + 1
            })

            logger.info(f"🎉 Workflow completed: {len(articles)} articles exported to {csv_path}")
            return state

        except Exception as e:
            logger.error(f"Exporter agent error: {str(e)}")
            current_task = state.get('current_task')
            if current_task:
                task = self.complete_task(current_task, {}, error=f"Export failed: {str(e)}")
                state = self.update_state(state, {
                    'current_task': task,
                    'is_complete': True,
                    'export_loop_count': state.get('export_loop_count', 0) + 1
                })
            return self.log_error(state, f"Export failed: {str(e)}")

# Singleton instances
search_agent = SearchAgent()
scraper_agent = ArticleAnalyzerAgent()
article_analyzer_agent = ArticleAnalyzerAgent()
exporter_agent = ExporterAgent()