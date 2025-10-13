"""
Types for the AutoData package.
Định nghĩa các types cho state management và message passing.
"""

from typing import TypedDict, List, Dict, Optional, Annotated, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class AgentRole(str, Enum):
    """Các vai trò của agents trong hệ thống"""
    MANAGER = "manager"
    WEB_CRAWLER = "web_crawler"
    PDF_HANDLER = "pdf_handler"
    CONTENT_EXTRACTOR = "content_extractor"
    SEARCH_AGENT = "search_agent"
    SCRAPER_AGENT = "scraper_agent"


class TaskStatus(str, Enum):
    """Trạng thái của task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(str, Enum):
    """Các loại task trong workflow"""
    CRAWL_WEB = "crawl_web"
    DOWNLOAD_PDF = "download_pdf"
    EXTRACT_CONTENT = "extract_content"
    SEARCH_OPINIONS = "search_opinions"
    SCRAPE_COMMENTS = "scrape_comments"  # Kept for backward compatibility
    SCRAPE_ARTICLES = "scrape_articles"  # New: scrape article content
    EXPORT_DATA = "export_data"


@dataclass
class Task:
    """Đại diện cho một task cần thực hiện"""
    task_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[AgentRole] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to.value if self.assigned_to else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class PDFDocument:
    """Thông tin về PDF document"""
    url: str
    local_path: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 0
    file_size: Optional[int] = None


@dataclass
class ExtractedKeywords:
    """Keywords được trích xuất từ PDF"""
    main_keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass
class Comment:
    """Đại diện cho một comment/ý kiến"""
    source: str  # Facebook, forum, news site, etc.
    source_url: str
    author: Optional[str] = None
    content: str = ""
    timestamp: Optional[datetime] = None
    likes: int = 0
    replies: int = 0
    sentiment: Optional[str] = None  # Để mở rộng cho phân tích cảm xúc
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "source_url": self.source_url,
            "author": self.author,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "likes": self.likes,
            "replies": self.replies,
            "sentiment": self.sentiment,
            "metadata": self.metadata
        }


class AgentState(TypedDict):
    """
    State được chia sẻ giữa các agents trong LangGraph.
    Đây là Local State approach - mỗi node có thể đọc/ghi state.
    """
    # Input ban đầu
    target_url: str  # URL của trang web cần crawl
    project_name: str  # Tên dự án để tracking

    # Workflow tracking
    current_task: Optional[Task]
    task_history: Annotated[List[Task], "History of all tasks"]
    current_agent: Optional[AgentRole]

    # PDF Document data
    pdf_document: Optional[PDFDocument]
    extracted_keywords: Optional[ExtractedKeywords]

    # Search & Scraping results
    search_queries: List[str]  # Các query được tạo từ keywords
    search_results: List[Dict[str, Any]]  # Kết quả tìm kiếm
    collected_comments: Annotated[List[Comment], "All collected comments"]

    # Article scraping and analysis
    analyzed_articles: Annotated[List[Dict[str, Any]], "Articles with sentiment analysis"]
    processed_urls: Annotated[set, "URLs that have been scraped"]
    scrape_articles_done: bool  # Flag to indicate scraping is complete
    scrape_loop_count: int  # Counter to prevent infinite loops
    export_loop_count: int  # Counter for export operations

    # Vector DB tracking
    vector_db_collection: Optional[str]  # Tên collection trong ChromaDB
    embedded_documents: List[str]  # IDs của documents đã embed

    # Output paths
    csv_output_path: Optional[str]
    pdf_local_path: Optional[str]

    # Error handling
    errors: Annotated[List[Dict[str, Any]], "Error log"]
    warnings: Annotated[List[str], "Warning messages"]

    # Metadata
    started_at: datetime
    last_updated: datetime
    is_complete: bool


@dataclass
class AgentMessage:
    """Message format để agents communicate"""
    from_agent: AgentRole
    to_agent: Optional[AgentRole]
    message_type: str  # "task_request", "task_complete", "error", "info"
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """Kết quả trả về từ tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


# Helper functions
def create_initial_state(target_url: str, project_name: str) -> AgentState:
    """Tạo initial state cho workflow"""
    now = datetime.now()
    return AgentState(
        target_url=target_url,
        project_name=project_name,
        current_task=None,
        task_history=[],
        current_agent=None,
        pdf_document=None,
        extracted_keywords=None,
        search_queries=[],
        search_results=[],
        collected_comments=[],
        analyzed_articles=[],
        processed_urls=set(),
        scrape_articles_done=False,
        scrape_loop_count=0,
        export_loop_count=0,
        vector_db_collection=None,
        embedded_documents=[],
        csv_output_path=None,
        pdf_local_path=None,
        errors=[],
        warnings=[],
        started_at=now,
        last_updated=now,
        is_complete=False
    )


def update_state_task(state: AgentState, task: Task) -> AgentState:
    """Helper để update task trong state"""
    state["current_task"] = task
    state["task_history"].append(task)
    state["last_updated"] = datetime.now()
    return state