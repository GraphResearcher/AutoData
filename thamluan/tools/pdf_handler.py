import requests
import os
from pathlib import Path
from typing import Optional
import logging
from urllib.parse import urlparse
import hashlib

from core.config import config
from core.types import ToolResult, PDFDocument

logger = logging.getLogger(__name__)


class PDFHandlerTool:
    """Tool để download và quản lý PDF files, cải thiện kiểm tra PDF thực sự."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })
        self.pdf_dir = Path(config.PDF_DIR)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    def download_pdf(self, url: str, filename: Optional[str] = None) -> ToolResult:
        """Download PDF từ URL nếu đúng là PDF."""
        try:
            logger.info(f"Downloading PDF from: {url}")

            # Generate filename nếu không có
            if not filename:
                parsed = urlparse(url)
                url_filename = os.path.basename(parsed.path)
                if url_filename.endswith('.pdf'):
                    filename = url_filename
                else:
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"document_{url_hash}.pdf"

            if not filename.endswith('.pdf'):
                filename += '.pdf'

            local_path = self.pdf_dir / filename

            # Nếu file tồn tại, kiểm tra valid PDF
            if local_path.exists():
                info_result = self.get_pdf_info(local_path)
                if info_result.success:
                    logger.info(f"PDF already exists and is valid: {local_path}")
                    return ToolResult(
                        success=True,
                        data={'local_path': str(local_path), 'filename': filename, 'already_exists': True}
                    )
                else:
                    logger.warning(f"Existing file invalid, re-downloading: {local_path}")
                    local_path.unlink()  # xóa file hỏng

            # Download PDF
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                logger.warning(f"URL may not be a PDF. Content-Type: {content_type}")
                return ToolResult(success=False, error=f"URL không phải PDF: {url}")

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"PDF downloaded successfully: {local_path}")
            return ToolResult(
                success=True,
                data={'local_path': str(local_path), 'filename': filename, 'already_exists': False}
            )

        except Exception as e:
            logger.error(f"Error downloading PDF: {str(e)}", exc_info=True)
            return ToolResult(success=False, error=str(e))

    def get_pdf_info(self, pdf_path: str) -> ToolResult:
        """Lấy thông tin cơ bản về PDF, kiểm tra valid PDF."""
        try:
            import PyPDF2
            path = Path(pdf_path)
            if not path.exists():
                return ToolResult(success=False, error=f"PDF file not found: {pdf_path}")

            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                metadata = reader.metadata or {}

            info = {
                'filename': path.name,
                'local_path': str(path),
                'num_pages': num_pages,
                'file_size': path.stat().st_size,
                'title': metadata.get('/Title', ''),
                'author': metadata.get('/Author', ''),
                'metadata': {k.replace('/', ''): v for k, v in metadata.items() if isinstance(v, str)}
            }

            logger.info(f"PDF info: {path.name} - {num_pages} pages - {info['file_size']} bytes")
            return ToolResult(success=True, data=info)

        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to read PDF: {str(e)}")

    def create_pdf_document(self, url: str, local_path: str) -> PDFDocument:
        info_result = self.get_pdf_info(local_path)
        if info_result.success:
            info = info_result.data
            return PDFDocument(
                url=url,
                local_path=local_path,
                title=info.get('title'),
                metadata=info.get('metadata', {}),
                page_count=info.get('num_pages', 0),
                file_size=info.get('file_size')
            )
        else:
            return PDFDocument(url=url, local_path=local_path)


# Singleton
pdf_handler_tool = PDFHandlerTool()
