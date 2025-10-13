"""
Development Agent Team - Xử lý các technical tasks.
Bao gồm: Web Crawler, PDF Handler, Content Extractor
"""

import logging
from typing import Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

from agents.base import BaseAgent
from core.types import AgentState, AgentRole, TaskType, PDFDocument
from tools import (
    web_crawler_tool,
    pdf_handler_tool,
    pdf_extractor_tool,
    vector_db_tool
)

from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class WebCrawlerAgent(BaseAgent):
    """
    Web Crawler Agent - Crawl web pages và tìm PDF links.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.WEB_CRAWLER,
            name="Web Crawler Agent",
            description="Crawls web pages and extracts PDF links"
        )

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"🕷️  {self.name} executing...")

            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.CRAWL_WEB:
                return state

            url = current_task.input_data.get('url') or state['target_url']
            logger.info(f"Crawling: {url}")

            if url.lower().endswith('.pdf'):
                pdf_links = [{'url': url, 'text': 'Direct PDF URL'}]
            else:
                pdf_result = web_crawler_tool.find_pdf_links(url)
                if not pdf_result.success:
                    task = self.complete_task(current_task, {}, error=pdf_result.error)
                    return self.update_state(state, {'current_task': task})
                pdf_links = pdf_result.data.get('pdf_links', [])

            logger.info(f"Found {len(pdf_links)} PDF links")
            if not pdf_links:
                error_msg = "No PDF links found on the page."
                return self.log_error(state, error_msg)

            first_pdf = pdf_links[0]
            pdf_url = first_pdf['url']
            logger.info(f"✅ Selected PDF: {pdf_url}")

            output_data = {
                'pdf_url': pdf_url,
                'pdf_links': pdf_links,
                'page_title': url
            }

            task = self.complete_task(current_task, output_data)
            state = self.update_state(state, {
                'current_task': task,
                'pdf_document': PDFDocument(url=pdf_url)
            })

            return state

        except Exception as e:
            logger.error(f"Web crawler error: {str(e)}", exc_info=True)
            return self.log_error(state, f"Web crawling failed: {str(e)}")


class PDFHandlerAgent(BaseAgent):
    """
    PDF Handler Agent - Download và xử lý PDF files.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.PDF_HANDLER,
            name="PDF Handler Agent",
            description="Downloads and manages PDF files"
        )

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"📥 {self.name} executing...")

            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.DOWNLOAD_PDF:
                return state

            pdf_document = state.get('pdf_document')
            if not pdf_document:
                return self.log_error(state, "No PDF URL found in state")

            pdf_url = pdf_document.url
            logger.info(f"Downloading PDF from: {pdf_url}")

            download_result = pdf_handler_tool.download_pdf(pdf_url)
            if not download_result.success:
                return self.log_error(state, download_result.error)

            local_path = download_result.data['local_path']
            logger.info(f"✅ PDF downloaded to: {local_path}")

            info_result = pdf_handler_tool.get_pdf_info(local_path)
            if not info_result.success:
                return self.log_error(state, info_result.error)

            pdf_doc = pdf_handler_tool.create_pdf_document(pdf_url, local_path)

            output_data = {
                'local_path': local_path,
                'file_size': info_result.data['file_size'],
                'page_count': info_result.data['num_pages']
            }

            task = self.complete_task(current_task, output_data)
            state = self.update_state(state, {
                'current_task': task,
                'pdf_document': pdf_doc,
                'pdf_local_path': local_path
            })

            return state

        except Exception as e:
            logger.error(f"PDF handler error: {str(e)}", exc_info=True)
            return self.log_error(state, f"PDF handling failed: {str(e)}")


class ContentExtractorAgent(BaseAgent):
    """
    Content Extractor Agent - Extract nội dung và keywords từ PDF,
    encode embeddings bằng SentenceTransformer và lưu vào VectorDB.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.CONTENT_EXTRACTOR,
            name="Content Extractor Agent",
            description="Extracts content, keywords, key phrases from PDFs and stores embeddings"
        )
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"📄 {self.name} executing...")

            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.EXTRACT_CONTENT:
                return state

            pdf_path = state.get('pdf_local_path')
            if not pdf_path:
                return self.log_error(state, "No PDF path found in state")

            logger.info(f"Extracting content from: {pdf_path}")

            extract_result = pdf_extractor_tool.extract_all(pdf_path)
            if not extract_result.success:
                return self.log_error(state, extract_result.error)

            extracted_keywords = extract_result.data['extracted_keywords']
            full_text = extract_result.data['full_text']

            logger.info(f"✅ Extracted {len(extracted_keywords.main_keywords)} keywords")
            logger.info(f"✅ Extracted {len(extracted_keywords.key_phrases)} key phrases")

            embedding = self.embedding_model.encode(full_text, convert_to_numpy=True)
            logger.info(f"✅ Generated embedding vector of length {len(embedding)}")

            collection_name = state['project_name'].replace(' ', '_')
            vector_db_tool.create_collection(collection_name)
            vector_db_tool.add_documents(
                collection_name=collection_name,
                documents=[full_text],
                embeddings=[embedding],
                metadatas=[{
                    'source': 'pdf',
                    'filename': pdf_path,
                    'type': 'draft_law'
                }],
                ids=['main_document']
            )
            logger.info(f"✅ Stored document in Vector DB: {collection_name}")

            output_data = {
                'keywords_count': len(extracted_keywords.main_keywords),
                'phrases_count': len(extracted_keywords.key_phrases),
                'text_length': len(full_text)
            }

            task = self.complete_task(current_task, output_data)
            state = self.update_state(state, {
                'current_task': task,
                'extracted_keywords': extracted_keywords,
                'vector_db_collection': collection_name,
                'embedded_documents': ['main_document']
            })

            pdf_doc = state['pdf_document']
            pdf_doc.content = full_text
            state['pdf_document'] = pdf_doc

            return state

        except Exception as e:
            logger.error(f"Content extractor error: {str(e)}", exc_info=True)
            return self.log_error(state, f"Content extraction failed: {str(e)}")


# Singleton instances
web_crawler_agent = WebCrawlerAgent()
pdf_handler_agent = PDFHandlerAgent()
content_extractor_agent = ContentExtractorAgent()
