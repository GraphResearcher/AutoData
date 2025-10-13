"""
Legal PDF Finder Tool - Tự động tìm kiếm và tải PDF Luật/Nghị định từ keywords.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, quote_plus
import re

from core.config import config
from core.types import ToolResult
from tools.search_engine import search_engine_tool
from tools.web_crawler import web_crawler_tool

logger = logging.getLogger(__name__)


class LegalPDFFinderTool:
    """Tool để tìm kiếm và phát hiện PDF Luật/Nghị định từ keywords"""
    
    # Danh sách các trang web chính thức về Luật/Nghị định Việt Nam
    LEGAL_DOMAINS = [
        'thuvienphapluat.vn',
        'luatvietnam.vn',
        'moj.gov.vn',  # Bộ Tư Pháp
        'chinhphu.vn',  # Cổng thông tin chính phủ
        'mpi.gov.vn',  # Bộ Kế hoạch và Đầu tư
        'mof.gov.vn',  # Bộ Tài chính
        'most.gov.vn',  # Bộ Khoa học và Công nghệ
        'mic.gov.vn',  # Bộ Thông tin và Truyền thông
        'na.gov.vn',  # Quốc hội
        'vietnamlawmagazine.vn',
        'mst.gov.vn',  # Bộ Tài chính
    ]
    
    # Từ khóa chỉ thị tài liệu luật
    LEGAL_INDICATORS = [
        'dự thảo',
        'luật',
        'nghị định',
        'thông tư',
        'quyết định',
        'nghị quyết',
        'văn bản',
        'pháp luật',
        'du thao',
        'nghi dinh',
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })

    def search_legal_pdfs(self, keywords: str, max_results: int = 10) -> ToolResult:
        """
        Tìm kiếm PDF Luật/Nghị định dựa trên keywords.
        
        Args:
            keywords: Từ khóa tìm kiếm (ví dụ: "Luật Khoa học công nghệ 2025")
            max_results: Số lượng kết quả tối đa
            
        Returns:
            ToolResult với danh sách PDF links tìm được
        """
        try:
            logger.info(f"🔍 Searching for legal PDFs with keywords: {keywords}")
            
            # Bước 1: Tạo search queries tối ưu
            search_queries = self._generate_legal_search_queries(keywords)
            logger.info(f"📋 Generated {len(search_queries)} search queries")
            
            # Bước 2: Tìm kiếm trên Google với site: operators
            all_results = []
            for query in search_queries[:3]:  # Giới hạn 3 queries để tránh rate limit
                logger.info(f"🔎 Searching: {query}")
                
                search_result = search_engine_tool.search(
                    query=query,
                    num_results=max_results,
                    search_engine="google"
                )
                
                if search_result.success:
                    results = search_result.data.get('results', [])
                    all_results.extend(results)
                    logger.info(f"  ✓ Found {len(results)} results")
                
                # Chờ một chút để tránh rate limit
                import time
                time.sleep(1)
            
            # Bước 3: Lọc và xếp hạng kết quả
            filtered_results = self._filter_legal_results(all_results, keywords)
            logger.info(f"📊 Filtered to {len(filtered_results)} relevant results")
            
            # Bước 4: Tìm PDF links từ các trang web
            pdf_links = []
            for result in filtered_results[:max_results]:
                url = result.get('url', '')
                logger.info(f"🔗 Checking URL: {url}")
                
                pdfs = self._extract_pdfs_from_url(url, keywords)
                if pdfs:
                    pdf_links.extend(pdfs)
                    logger.info(f"  ✓ Found {len(pdfs)} PDF(s)")
                
                # Dừng nếu đã có đủ kết quả
                if len(pdf_links) >= max_results:
                    break
            
            # Loại bỏ trùng lặp
            unique_pdfs = self._deduplicate_pdfs(pdf_links)
            logger.info(f"✅ Total unique PDFs found: {len(unique_pdfs)}")
            
            return ToolResult(
                success=True,
                data={
                    'pdf_links': unique_pdfs[:max_results],
                    'total_found': len(unique_pdfs),
                    'search_queries': search_queries
                }
            )
            
        except Exception as e:
            logger.error(f"Legal PDF search error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to search legal PDFs: {str(e)}"
            )

    def _generate_legal_search_queries(self, keywords: str) -> List[str]:
        """Tạo các search queries tối ưu cho tìm kiếm luật"""
        queries = []
        
        # Query 1: Tìm trên các site chính thức với "filetype:pdf"
        site_operators = ' OR '.join([f'site:{domain}' for domain in self.LEGAL_DOMAINS[:5]])
        queries.append(f'{keywords} filetype:pdf ({site_operators})')
        
        # Query 2: Tìm dự thảo + PDF
        queries.append(f'dự thảo {keywords} filetype:pdf')
        
        # Query 3: Tìm với từ khóa "tải về" hoặc "download"
        queries.append(f'{keywords} (tải về OR download) PDF')
        
        # Query 4: Tìm văn bản pháp luật
        queries.append(f'văn bản {keywords} PDF site:thuvienphapluat.vn OR site:luatvietnam.vn')
        
        # Query 5: Tìm trên trang Chính phủ/Bộ
        queries.append(f'{keywords} PDF site:chinhphu.vn OR site:moj.gov.vn OR site:most.gov.vn')
        
        return queries

    def _filter_legal_results(self, results: List[Dict], keywords: str) -> List[Dict]:
        """Lọc và xếp hạng kết quả theo độ liên quan"""
        filtered = []
        keywords_lower = keywords.lower()
        
        for result in results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # Kiểm tra có chứa domain legal không
            is_legal_domain = any(domain in url for domain in self.LEGAL_DOMAINS)
            
            # Kiểm tra có chứa indicators không
            has_legal_indicator = any(indicator in title or indicator in snippet 
                                     for indicator in self.LEGAL_INDICATORS)
            
            # Kiểm tra có chứa keywords không
            has_keywords = any(word in title or word in snippet 
                              for word in keywords_lower.split())
            
            # Tính điểm
            score = 0
            if is_legal_domain:
                score += 10
            if has_legal_indicator:
                score += 5
            if has_keywords:
                score += 3
            if 'pdf' in url or 'pdf' in title:
                score += 7
            if 'dự thảo' in title or 'du thao' in title:
                score += 5
            
            # Chỉ giữ kết quả có điểm >= 8
            if score >= 8:
                result['relevance_score'] = score
                filtered.append(result)
        
        # Sắp xếp theo điểm giảm dần
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return filtered

    def _extract_pdfs_from_url(self, url: str, keywords: str) -> List[Dict[str, str]]:
        """Trích xuất PDF links từ một URL"""
        try:
            # Sử dụng web_crawler_tool để tìm PDF
            result = web_crawler_tool.find_pdf_links(url)
            
            if not result.success:
                return []
            
            pdf_links = result.data.get('pdf_links', [])
            
            # Lọc PDF links liên quan đến keywords
            keywords_lower = keywords.lower()
            relevant_pdfs = []
            
            for pdf in pdf_links:
                pdf_url = pdf.get('url', '')
                pdf_text = pdf.get('text', '').lower()
                
                # Kiểm tra liên quan
                is_relevant = any(word in pdf_text or word in pdf_url.lower() 
                                 for word in keywords_lower.split())
                
                # Hoặc chứa legal indicators
                has_legal = any(indicator in pdf_text or indicator in pdf_url.lower()
                               for indicator in self.LEGAL_INDICATORS)
                
                if is_relevant or has_legal:
                    relevant_pdfs.append(pdf)
            
            return relevant_pdfs if relevant_pdfs else pdf_links[:3]  # Fallback: lấy 3 PDFs đầu
            
        except Exception as e:
            logger.error(f"Error extracting PDFs from {url}: {str(e)}")
            return []

    def _deduplicate_pdfs(self, pdf_links: List[Dict]) -> List[Dict]:
        """Loại bỏ PDF trùng lặp"""
        seen_urls = set()
        unique_pdfs = []
        
        for pdf in pdf_links:
            url = pdf.get('url', '')
            # Chuẩn hóa URL (bỏ fragment và query params để so sánh)
            normalized_url = url.split('?')[0].split('#')[0]
            
            if normalized_url and normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_pdfs.append(pdf)
        
        return unique_pdfs

    def find_best_pdf(self, keywords: str) -> ToolResult:
        """
        Tìm PDF tốt nhất cho keywords.
        
        Args:
            keywords: Từ khóa tìm kiếm
            
        Returns:
            ToolResult với PDF link tốt nhất
        """
        result = self.search_legal_pdfs(keywords, max_results=5)
        
        if not result.success:
            return result
        
        pdf_links = result.data.get('pdf_links', [])
        
        if not pdf_links:
            return ToolResult(
                success=False,
                error="No PDF found for the given keywords"
            )
        
        # Trả về PDF đầu tiên (có điểm cao nhất)
        best_pdf = pdf_links[0]
        
        return ToolResult(
            success=True,
            data={
                'pdf_link': best_pdf,
                'alternatives': pdf_links[1:3] if len(pdf_links) > 1 else []
            }
        )


# Singleton instance
legal_pdf_finder_tool = LegalPDFFinderTool()
