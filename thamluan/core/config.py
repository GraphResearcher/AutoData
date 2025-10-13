"""
Configuration settings for AutoData system.
Quản lý tất cả các settings, API keys, paths, và parameters.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Main configuration class"""

    # ========== Paths ==========
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    PDF_DIR = DATA_DIR / "pdfs"
    CSV_DIR = DATA_DIR / "csv"
    LOGS_DIR = BASE_DIR / "logs"
    VECTOR_DB_DIR = DATA_DIR / "vector_db"

    # Tạo các thư mục nếu chưa tồn tại
    for dir_path in [DATA_DIR, PDF_DIR, CSV_DIR, LOGS_DIR, VECTOR_DB_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # ========== LLM Settings ==========
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # ========== Embedding Settings ==========
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

    # ========== Vector DB Settings ==========
    VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chromadb")
    CHROMA_PERSIST_DIR = str(VECTOR_DB_DIR / "chroma")
    VECTOR_DB_COLLECTION_PREFIX = "autodata"

    # ========== Web Scraping Settings ==========
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

    # Selenium settings
    SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
    SELENIUM_WAIT_TIME = int(os.getenv("SELENIUM_WAIT_TIME", "10"))

    # ========== PDF Processing Settings ==========
    PDF_MAX_SIZE_MB = int(os.getenv("PDF_MAX_SIZE_MB", "50"))
    PDF_EXTRACT_IMAGES = os.getenv("PDF_EXTRACT_IMAGES", "false").lower() == "true"

    # ========== Search Settings ==========
    # Google Search
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
    GOOGLE_SEARCH_MAX_RESULTS = int(os.getenv("GOOGLE_SEARCH_MAX_RESULTS", "20"))

    # Search sources priority (dễ crawl trước)
    SEARCH_SOURCES_PRIORITY = [
        "google",  # Google search results
        "news",  # News websites
        "forums",  # Vietnamese forums
        # "facebook",  # Facebook (khó crawl hơn, để sau)
    ]

    # ========== Comment Scraping Settings ==========
    MAX_COMMENTS_PER_SOURCE = int(os.getenv("MAX_COMMENTS_PER_SOURCE", "100"))
    COMMENT_MIN_LENGTH = int(os.getenv("COMMENT_MIN_LENGTH", "10"))

    # ========== Keyword Extraction Settings ==========
    MIN_KEYWORD_LENGTH = int(os.getenv("MIN_KEYWORD_LENGTH", "3"))
    MAX_KEYWORDS = int(os.getenv("MAX_KEYWORDS", "50"))
    MIN_KEYWORD_FREQUENCY = int(os.getenv("MIN_KEYWORD_FREQUENCY", "2"))

    # Vietnamese stopwords có thể thêm vào
    VIETNAMESE_STOPWORDS = set([
        "và", "của", "có", "trong", "được", "cho", "về", "với", "này",
        "đó", "các", "những", "để", "từ", "theo", "trên", "không", "là",
        "thì", "sẽ", "đã", "đang", "khi", "nếu", "hoặc", "nhưng", "vì"
    ])

    # ========== Export Settings ==========
    CSV_ENCODING = os.getenv("CSV_ENCODING", "utf-8-sig")  # utf-8-sig để Excel đọc được
    CSV_DELIMITER = os.getenv("CSV_DELIMITER", ",")

    # ========== Logging Settings ==========
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", "10485760"))  # 10MB
    LOG_FILE_BACKUP_COUNT = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))

    # ========== Agent Settings ==========
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
    AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "300"))

    # ========== Development Settings ==========
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    SAVE_INTERMEDIATE_RESULTS = os.getenv(
        "SAVE_INTERMEDIATE_RESULTS", "true"
    ).lower() == "true"

    # ========== Target Domains ==========
    # Danh sách các trang tin tức/diễn đàn Việt Nam có thể crawl
    TRUSTED_DOMAINS = [
        "vnexpress.net",
        "tuoitre.vn",
        "thanhnien.vn",
        "dantri.com.vn",
        "vietnamnet.vn",
        "baomoi.com",
        "tienphong.vn",
        "mst.gov.vn",  # Trang web chính thức
    ]

    @classmethod
    def get_pdf_path(cls, filename: str) -> Path:
        """Lấy đường dẫn đầy đủ cho PDF file"""
        return cls.PDF_DIR / filename

    @classmethod
    def get_csv_path(cls, filename: str) -> Path:
        """Lấy đường dẫn đầy đủ cho CSV file"""
        return cls.CSV_DIR / filename

    @classmethod
    def get_log_path(cls, filename: str) -> Path:
        """Lấy đường dẫn đầy đủ cho log file"""
        return cls.LOGS_DIR / filename

    @classmethod
    def validate_config(cls) -> bool:
        """Kiểm tra config có hợp lệ không"""
        issues = []

        # Kiểm tra Ollama connection
        try:
            import requests
            response = requests.get(f"{cls.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                issues.append(f"Cannot connect to Ollama at {cls.OLLAMA_BASE_URL}")
        except Exception as e:
            issues.append(f"Ollama connection error: {str(e)}")

        # Kiểm tra model có tồn tại không
        try:
            import requests
            response = requests.get(f"{cls.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                if cls.LLM_MODEL not in models:
                    issues.append(
                        f"Model {cls.LLM_MODEL} not found. "
                        f"Available models: {', '.join(models)}"
                    )
        except Exception:
            pass  # Already logged connection error above

        if issues:
            print("⚠️  Configuration Issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        return True

    @classmethod
    def display_config(cls):
        """Hiển thị config hiện tại"""
        print("=" * 60)
        print("AutoData Configuration")
        print("=" * 60)
        print(f"LLM Model: {cls.LLM_MODEL}")
        print(f"Ollama URL: {cls.OLLAMA_BASE_URL}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"PDF Directory: {cls.PDF_DIR}")
        print(f"CSV Directory: {cls.CSV_DIR}")
        print(f"Vector DB: {cls.VECTOR_DB_TYPE} at {cls.CHROMA_PERSIST_DIR}")
        print(f"Debug Mode: {cls.DEBUG_MODE}")
        print("=" * 60)


# Singleton instance
config = Config()

# Export
__all__ = ["Config", "config"]