"""
Tools package for AutoData system.
Chứa tất cả các tools để agents sử dụng.
"""

from .web_crawler import WebCrawlerTool
from .pdf_handler import PDFHandlerTool
from .pdf_extractor import PDFExtractorTool
from .search_engine import SearchEngineTool
from .comment_scraper import CommentScraperTool
from .csv_exporter import CSVExporterTool
from .text_analyzer import TextAnalyzerTool
from .vector_db import VectorDBTool
from .article_scraper import ArticleScraperTool, article_scraper_tool
from .sentiment_analyzer import SentimentAnalyzerTool, sentiment_analyzer_tool

web_crawler_tool = WebCrawlerTool()
pdf_handler_tool = PDFHandlerTool()
pdf_extractor_tool = PDFExtractorTool()
search_engine_tool = SearchEngineTool()
comment_scraper_tool = CommentScraperTool()
csv_exporter_tool = CSVExporterTool()
text_analyzer_tool = TextAnalyzerTool()
vector_db_tool = VectorDBTool()
