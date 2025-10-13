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
    
    # Danh sách các trang web chính thức về Luật/Nghị định Việt Nam (ƯU TIÊN)
    PRIORITY_LEGAL_DOMAINS = [
        'duthaoonline.quochoi.vn',  # Dự thảo online Quốc hội - ƯU TIÊN HÀNG ĐẦU
        'thuvienphapluat.vn',  # Thư viện Pháp luật
        'baochinhphu.vn',  # Báo Chính phủ
    ]
    
    # Các trang web chính thức khác
    LEGAL_DOMAINS = [
        'duthaoonline.quochoi.vn',
        'thuvienphapluat.vn',
        'baochinhphu.vn',
        'luatvietnam.vn',
        'moj.gov.vn',  # Bộ Tư Pháp
        'chinhphu.vn',  # Cổng thông tin chính phủ
        'mpi.gov.vn',  # Bộ Kế hoạch và Đầu tư
        'mof.gov.vn',  # Bộ Tài chính
        'most.gov.vn',  # Bộ Khoa học và Công nghệ
        'mic.gov.vn',  # Bộ Thông tin và Truyền thông
        'na.gov.vn',  # Quốc hội
        'vietnamlawmagazine.vn',
        'mst.gov.vn',
    ]
    
    # URL trực tiếp để crawl
    DIRECT_CRAWL_URLS = [
        'https://duthaoonline.quochoi.vn/du-thao/du-thao-luat',
        'https://baochinhphu.vn/',
        'https://thuvienphapluat.vn/',
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
        self.crawl4ai_available = False
        try:
            from crawl4ai import WebCrawler
            self.crawl4ai_available = True
            logger.info("✅ Crawl4AI available for advanced crawling")
        except ImportError:
            logger.info("ℹ️ Crawl4AI not available, using standard crawling")

    def search_legal_pdfs_direct_crawl(self, keywords: str, max_results: int = 10) -> ToolResult:
        """
        Tìm kiếm PDF bằng cách crawl trực tiếp các trang web uy tín.
        Phương pháp này CHÍNH XÁC hơn Google search.
        """
        try:
            logger.info(f"🔍 Direct crawling trusted sites for keywords: {keywords}")
            all_pdfs = []
            
            # Bước 1: Crawl trực tiếp các trang ưu tiên
            priority_sites = [
                {
                    'name': 'Dự thảo Online Quốc hội',
                    'url': 'https://duthaoonline.quochoi.vn/du-thao/du-thao-luat',
                    'search_url': f'https://duthaoonline.quochoi.vn/DuThao/Lists/DT_DUTHAO_NGHIQUYET/?keyword={quote_plus(keywords)}'
                },
                {
                    'name': 'Thư viện Pháp luật',
                    'url': 'https://thuvienphapluat.vn/',
                    'search_url': f'https://thuvienphapluat.vn/van-ban/tim-van-ban.aspx?keyword={quote_plus(keywords)}&Page=1'
                },
                {
                    'name': 'Báo Chính phủ',
                    'url': 'https://baochinhphu.vn/',
                    'search_url': f'https://baochinhphu.vn/tim-kiem.htm?keywords={quote_plus(keywords)}'
                }
            ]
            
            for site in priority_sites:
                logger.info(f"📰 Crawling {site['name']}...")
                try:
                    pdfs = self._crawl_site_for_pdfs(site['search_url'], keywords, site['name'])
                    if pdfs:
                        all_pdfs.extend(pdfs)
                        logger.info(f"  ✓ Found {len(pdfs)} PDF(s) from {site['name']}")
                except Exception as e:
                    logger.warning(f"  ✗ Failed to crawl {site['name']}: {str(e)}")
                    continue
            
            # Loại bỏ trùng lặp
            unique_pdfs = self._deduplicate_pdfs(all_pdfs)
            logger.info(f"✅ Total unique PDFs from direct crawling: {len(unique_pdfs)}")
            
            return ToolResult(
                success=True,
                data={
                    'pdf_links': unique_pdfs[:max_results],
                    'total_found': len(unique_pdfs),
                    'method': 'direct_crawl'
                }
            )
            
        except Exception as e:
            logger.error(f"Direct crawl error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to crawl sites directly: {str(e)}"
            )
    
    def _crawl_site_for_pdfs(self, url: str, keywords: str, site_name: str) -> List[Dict[str, str]]:
        """Crawl một trang web để tìm PDF"""
        try:
            # Thử dùng crawl4ai nếu có
            if self.crawl4ai_available:
                return self._crawl_with_crawl4ai(url, keywords, site_name)
            else:
                # Fallback: dùng web_crawler_tool
                return self._crawl_with_standard_tool(url, keywords, site_name)
        except Exception as e:
            logger.error(f"Error crawling {site_name}: {str(e)}")
            return []
    
    def _crawl_with_crawl4ai(self, url: str, keywords: str, site_name: str) -> List[Dict[str, str]]:
        """Sử dụng crawl4ai để crawl (advanced)"""
        try:
            from crawl4ai import WebCrawler
            
            crawler = WebCrawler()
            result = crawler.run(url=url)
            
            if not result.success:
                logger.warning(f"Crawl4AI failed for {url}")
                return self._crawl_with_standard_tool(url, keywords, site_name)
            
            # Parse HTML với BeautifulSoup
            soup = BeautifulSoup(result.html, 'lxml')
            
            # Tìm tất cả links
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                # Check nếu là PDF
                if href.lower().endswith('.pdf') or 'pdf' in href.lower():
                    full_url = urljoin(url, href)
                    
                    # Check relevance với keywords
                    if self._is_relevant_to_keywords(text, href, keywords):
                        pdf_links.append({
                            'url': full_url,
                            'text': text or f'PDF from {site_name}',
                            'source': site_name
                        })
            
            return pdf_links
            
        except Exception as e:
            logger.error(f"Crawl4AI error: {str(e)}")
            return self._crawl_with_standard_tool(url, keywords, site_name)
    
    def _crawl_with_standard_tool(self, url: str, keywords: str, site_name: str) -> List[Dict[str, str]]:
        """Sử dụng web_crawler_tool tiêu chuẩn"""
        try:
            result = web_crawler_tool.find_pdf_links(url)
            
            if not result.success:
                return []
            
            pdf_links = result.data.get('pdf_links', [])
            
            # Filter relevant PDFs
            relevant_pdfs = []
            for pdf in pdf_links:
                if self._is_relevant_to_keywords(pdf.get('text', ''), pdf.get('url', ''), keywords):
                    pdf['source'] = site_name
                    relevant_pdfs.append(pdf)
            
            return relevant_pdfs
            
        except Exception as e:
            logger.error(f"Standard crawl error: {str(e)}")
            return []
    
    def _is_relevant_to_keywords(self, text: str, url: str, keywords: str) -> bool:
        """Kiểm tra xem text/url có liên quan đến keywords không"""
        text_lower = text.lower()
        url_lower = url.lower()
        keywords_lower = keywords.lower()
        
        # Check từng từ trong keywords
        keyword_words = keywords_lower.split()
        matches = sum(1 for word in keyword_words if word in text_lower or word in url_lower)
        
        # Cần ít nhất 40% từ khóa match hoặc có legal indicators
        threshold = len(keyword_words) * 0.4
        has_match = matches >= max(1, threshold)
        
        # Hoặc chứa legal indicators
        has_legal = any(indicator in text_lower or indicator in url_lower 
                       for indicator in self.LEGAL_INDICATORS)
        
        return has_match or has_legal

    def search_legal_pdfs(self, keywords: str, max_results: int = 10) -> ToolResult:
        """
        Tìm kiếm PDF Luật/Nghị định dựa trên keywords.
        CHIẾN LƯỢC: Ưu tiên crawl trực tiếp các trang uy tín, sau đó mới dùng Google search.
        
        Args:
            keywords: Từ khóa tìm kiếm (ví dụ: "Luật Khoa học công nghệ 2025")
            max_results: Số lượng kết quả tối đa
            
        Returns:
            ToolResult với danh sách PDF links tìm được
        """
        try:
            logger.info(f"🔍 Searching for legal PDFs with keywords: {keywords}")
            
            # CHIẾN LƯỢC 1: Crawl trực tiếp các trang uy tín TRƯỚC (CHÍNH XÁC NHẤT)
            logger.info("📍 Strategy 1: Direct crawling trusted Vietnamese legal sites...")
            direct_result = self.search_legal_pdfs_direct_crawl(keywords, max_results)
            
            if direct_result.success and len(direct_result.data.get('pdf_links', [])) > 0:
                logger.info(f"✅ Found {len(direct_result.data['pdf_links'])} PDFs from direct crawling")
                # Nếu tìm được đủ PDFs từ direct crawl, return luôn
                if len(direct_result.data['pdf_links']) >= max_results:
                    return direct_result
                
                # Nếu chưa đủ, lưu lại và tiếp tục với Google search
                direct_pdfs = direct_result.data['pdf_links']
            else:
                logger.info("⚠️ Direct crawling found no PDFs, trying Google search...")
                direct_pdfs = []
            
            # CHIẾN LƯỢC 2: Google search (FALLBACK)
            logger.info("📍 Strategy 2: Google search on legal domains...")
            search_queries = self._generate_legal_search_queries(keywords)
            logger.info(f"📋 Generated {len(search_queries)} search queries")
            
            all_results = []
            for query in search_queries[:3]:  # Giới hạn 3 queries
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
                
                import time
                time.sleep(1)
            
            # Lọc và xếp hạng kết quả từ Google
            filtered_results = self._filter_legal_results(all_results, keywords)
            logger.info(f"📊 Filtered to {len(filtered_results)} relevant Google results")
            
            # Tìm PDF links từ các trang web (Google results)
            google_pdfs = []
            for result in filtered_results[:max_results]:
                url = result.get('url', '')
                logger.info(f"🔗 Checking URL: {url}")
                
                pdfs = self._extract_pdfs_from_url(url, keywords)
                if pdfs:
                    google_pdfs.extend(pdfs)
                    logger.info(f"  ✓ Found {len(pdfs)} PDF(s)")
                
                if len(google_pdfs) >= max_results:
                    break
            
            # Kết hợp kết quả: Direct crawl PDFs ƯU TIÊN trước, sau đó Google PDFs
            all_pdfs = direct_pdfs + google_pdfs
            
            # Loại bỏ trùng lặp
            unique_pdfs = self._deduplicate_pdfs(all_pdfs)
            logger.info(f"✅ Total unique PDFs found: {len(unique_pdfs)} (Direct: {len(direct_pdfs)}, Google: {len(google_pdfs)})")
            
            return ToolResult(
                success=True,
                data={
                    'pdf_links': unique_pdfs[:max_results],
                    'total_found': len(unique_pdfs),
                    'search_queries': search_queries,
                    'direct_count': len(direct_pdfs),
                    'google_count': len(google_pdfs)
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
        
        # Query 1: Ưu tiên các trang VIP nhất - Dự thảo Quốc hội, Thư viện Pháp luật, Báo Chính phủ
        priority_sites = ' OR '.join([f'site:{domain}' for domain in self.PRIORITY_LEGAL_DOMAINS])
        queries.append(f'{keywords} filetype:pdf ({priority_sites})')
        
        # Query 2: Tìm dự thảo luật cụ thể trên Quốc hội
        queries.append(f'dự thảo {keywords} filetype:pdf site:duthaoonline.quochoi.vn')
        
        # Query 3: Tìm trên Thư viện Pháp luật
        queries.append(f'{keywords} filetype:pdf site:thuvienphapluat.vn')
        
        # Query 4: Tìm trên Báo Chính phủ
        queries.append(f'{keywords} filetype:pdf site:baochinhphu.vn')
        
        # Query 5: Tìm trên các site chính thức khác
        other_sites = ' OR '.join([f'site:{domain}' for domain in self.LEGAL_DOMAINS[3:8]])
        queries.append(f'{keywords} filetype:pdf ({other_sites})')
        
        # Query 6: Tìm với từ khóa dự thảo + nghị định
        queries.append(f'dự thảo nghị định {keywords} filetype:pdf')
        
        return queries

    def _filter_legal_results(self, results: List[Dict], keywords: str) -> List[Dict]:
        """Lọc và xếp hạng kết quả theo độ liên quan"""
        filtered = []
        keywords_lower = keywords.lower()
        
        for result in results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # Kiểm tra có chứa PRIORITY domain không (ƯU TIÊN CAO NHẤT)
            is_priority_domain = any(domain in url for domain in self.PRIORITY_LEGAL_DOMAINS)
            
            # Kiểm tra có chứa domain legal không
            is_legal_domain = any(domain in url for domain in self.LEGAL_DOMAINS)
            
            # Kiểm tra có chứa indicators không
            has_legal_indicator = any(indicator in title or indicator in snippet 
                                     for indicator in self.LEGAL_INDICATORS)
            
            # Kiểm tra có chứa keywords không
            keyword_words = keywords_lower.split()
            keyword_matches = sum(1 for word in keyword_words if word in title or word in snippet)
            has_keywords = keyword_matches > 0
            
            # Tính điểm
            score = 0
            if is_priority_domain:
                score += 20  # Điểm cực cao cho các trang ưu tiên
            elif is_legal_domain:
                score += 10
            
            if has_legal_indicator:
                score += 5
            
            # Điểm keywords theo tỷ lệ match
            score += keyword_matches * 2
            
            if 'pdf' in url or 'pdf' in title:
                score += 7
            
            if 'dự thảo' in title or 'du thao' in title or 'du-thao' in url:
                score += 8  # Tăng điểm cho dự thảo
            
            if 'quochoi.vn' in url or 'duthaoonline' in url:
                score += 15  # Bonus cho Quốc hội
            
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
