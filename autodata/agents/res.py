# autodata/agents/res.py
import sys
import re
import json
import logging
from typing import Callable, Union, Optional, List, Dict, Any
from autodata.tools.pdf import extract_text_from_pdf
from autodata.tools.legal import split_into_articles
from autodata.tools.keywords import extract_keywords
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from easydict import EasyDict
from autodata.core.types import AgentState
from autodata.prompts.prompt_loader import load_prompt
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from autodata.agents.base import BaseAgent, BaseResponse
from autodata.agents.base import BaseAgent, BaseResponse
from autodata.tools.web import get_page_content, normalize_url
from autodata.tools.search import search_discussions
from autodata.tools.crawler import crawl_comments_from_url
from autodata.tools.csv_utils import save_results_csv
logger = logging.getLogger(__name__)

sys.dont_write_bytecode = True
logger = logging.getLogger(__name__)


class BrowserAction(BaseResponse):
    action: str = Field(description="Type of browser action", pattern="^(search|open|extract|click|scroll|get_pdf_links|download_pdf|extract_pdf_text|extract_keywords|search_discussions|crawl_comments|save_csv)$")
    query: Optional[str] = Field(None, description="Search query if action==search or search_discussions")
    url: Optional[str] = Field(None, description="URL for open/extract/download_pdf/crawl_comments")
    selector: Optional[str] = Field(None, description="CSS selector if needed")
    path: Optional[str] = Field(None, description="Local path (for downloads or save)")
    num_results: Optional[int] = Field(5, description="Number of results to fetch")
    notes: Optional[str] = Field(None, description="Optional notes")


class Step(BaseResponse):
    name: str = Field(description="The name of the step.")
    description: str = Field(description="The description of the step.")
    output: str = Field(description="The expected output of the step.")


class PlannerResponse(BaseResponse):
    thought: str = Field(description="A thinking step to complete the given user task.")
    steps: List[Step] = Field(description="A list of detailed steps to complete the task.")

class CrawlSource(BaseModel):
    source_name: str = Field(..., description="Tên nguồn thông tin (ví dụ: Báo Chính phủ, Dân trí, Facebook, Reddit)")
    base_url: str = Field(..., description="URL gốc của nguồn cần crawl")
    search_query: str = Field(..., description="Truy vấn cụ thể dùng để tìm bài viết, ví dụ 'ý kiến dự thảo luật khoa học 2025 site:dantri.com.vn'")
    crawl_priority: int = Field(..., description="Mức độ ưu tiên crawl (1=quan trọng nhất, 5=phụ)")
    expected_data_type: str = Field(..., description="Loại dữ liệu dự kiến: 'bình luận', 'bài viết', 'phân tích', ...")

class BlueprintResponse(BaseResponse):
    status: str = Field(..., description="Trạng thái xử lý: success hoặc error")
    topic_summary: Optional[str] = Field(None, description="Tóm tắt nội dung dự thảo nhận từ ToolAgent")
    keywords: List[str] = Field(default_factory=list, description="Danh sách từ khóa chính về dự thảo")
    sources: List[CrawlSource] = Field(default_factory=list, description="Danh sách nguồn và truy vấn đề xuất để crawl")
    total_sources: int = Field(0, description="Tổng số nguồn được sinh ra")

class ArticleSummary(BaseModel):
    article_no: Optional[int] = Field(None, description="Số điều trong văn bản")
    title: Optional[str] = Field(None, description="Tiêu đề của điều luật")
    summary: str = Field(..., description="Tóm tắt nội dung điều luật bằng tiếng Việt")
    keywords: List[str] = Field(default_factory=list, description="Các từ khóa chính của điều luật")
    content: str = Field(..., description="Nội dung gốc của điều luật")

class ToolResponse(BaseResponse):
    status: str = Field(..., description="Trạng thái xử lý: success hoặc error")
    source_url: Optional[str] = Field(None, description="Đường dẫn PDF nguồn")
    article_count: int = Field(0, description="Số lượng điều được trích xuất")
    summary: Optional[str] = Field(None, description="Tóm tắt toàn văn tài liệu")
    articles: List[ArticleSummary] = Field(default_factory=list, description="Danh sách điều được trích xuất")

class ResultItem(BaseModel):
    title: Optional[str] = Field(None, description="Tiêu đề trang / bài viết")
    link: str = Field(..., description="URL bài viết")
    snippet: Optional[str] = Field(None, description="Đoạn mô tả / snippet")
    comments_count: int = Field(0, description="Số comment thu thập được (ước tính)")
    sample_comments: List[str] = Field(default_factory=list, description="Một vài comment mẫu")


class SourceResult(BaseModel):
    source_name: Optional[str] = Field(None, description="Tên nguồn (vd: Dân trí, Vnexpress)")
    base_url: Optional[str] = Field(None, description="URL gốc nguồn")
    search_query: Optional[str] = Field(None, description="Truy vấn tìm kiếm đã dùng")
    crawl_priority: Optional[int] = Field(3, description="Độ ưu tiên")
    expected_data_type: Optional[str] = Field(None, description="Loại dữ liệu mong đợi")
    results: List[ResultItem] = Field(default_factory=list, description="Danh sách kết quả (bài viết / thread)")


class WebAgentResponse(BaseResponse):
    status: str = Field(..., description="success hoặc error")
    processed_sources: int = Field(0, description="Số nguồn đã xử lý")
    total_links_found: int = Field(0, description="Tổng số link tìm được")
    total_comments_collected: int = Field(0, description="Tổng số comment đã thu thập")
    sources: List[SourceResult] = Field(default_factory=list, description="Kết quả chi tiết theo nguồn")
    saved_csv: Optional[str] = Field(None, description="Đường dẫn file CSV nếu đã lưu")

# --------------------
# PlannerAgent
# --------------------
class PlannerAgent(BaseAgent):
    def __init__(self, agent_name: str = "PlannerAgent", description: str = "A planner agent to plan the data collection process.", model: Callable = None, tools=None, **kwargs):
        parser = PydanticOutputParser(pydantic_object=PlannerResponse)
        format_instr = parser.get_format_instructions()
        instruction = (
            "You are a Planning Agent.\n"
            "Your ONLY output must be valid JSON conforming to the schema below.\n\n"
            f"{load_prompt('planner')}\n\n{format_instr}\n\nReturn ONLY the JSON object."
        )

        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=parser,
        )
        logger.info("PlannerAgent initialized successfully")


# --------------------
# ToolAgent (thực thi hành động)
# --------------------

class ToolAgent(BaseAgent):
    """
    ToolAgent — tự động tải PDF từ URL, trích xuất nội dung, phân tích và tóm tắt văn bản pháp luật tiếng Việt.
    """

    def __init__(
        self,
        agent_name: str = "ToolAgent",
        description: str = "Agent chịu trách nhiệm sử dụng các công cụ để hoàn thành tác vụ cụ thể.",
        model=None,
        tools=None,
        output_parser=None,
        **kwargs,
    ):
        # 🔹 Load prompt tool.md
        instruction = load_prompt("tool")

        super().__init__(
            agent_name=agent_name,
            instruction=instruction,  # <--- quan trọng, thiếu dòng này sẽ lỗi
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
            **kwargs,
        )
        logger.info("ToolAgent initialized successfully")
    # ======================================================
    # MAIN FUNCTION
    # ======================================================
    async def run(self, input_data: Dict[str, Any]) -> ToolResponse:
        """
        input_data example:
        {
            "pdf_url": "https://mst.gov.vn/du-thao/2256.pdf"
        }
        """
        try:
            logger.info("[ToolAgent] Bắt đầu xử lý PDF...")

            pdf_url = input_data.get("pdf_url")
            if not pdf_url:
                raise ValueError("Thiếu trường 'pdf_url' trong input_data")

            pdf_bytes = self._download_pdf(pdf_url)
            if not pdf_bytes:
                raise ValueError("Không thể tải file PDF từ URL.")

            # 1️⃣ Trích xuất văn bản từ PDF
            text = extract_text_from_pdf(pdf_bytes)
            if not text or len(text) < 200:
                raise ValueError("Không thể trích xuất nội dung hợp lệ từ PDF.")

            # 2️⃣ Phân tách văn bản thành các 'Điều'
            articles = split_into_articles(text)
            if not articles:
                raise ValueError("Không tìm thấy cấu trúc 'Điều' trong văn bản.")

            # 3️⃣ Trích xuất từ khóa và tóm tắt từng điều
            parsed_articles = []
            for art in articles:
                art_kw = extract_keywords(art["content"], top_n=8)
                art_summary = await self._summarize_article(art["content"])
                parsed_articles.append(
                    ArticleSummary(
                        article_no=art.get("article_no"),
                        title=art.get("title"),
                        summary=art_summary,
                        keywords=art_kw,
                        content=art.get("content", "")
                    )
                )

            # 4️⃣ Tóm tắt toàn bộ văn bản
            global_summary = await self._summarize_whole_text(text)

            return ToolResponse(
                status="success",
                source_url=pdf_url,
                article_count=len(parsed_articles),
                summary=global_summary,
                articles=parsed_articles,
            )

        except Exception as e:
            logger.error(f"[ToolAgent] Lỗi khi xử lý PDF: {e}")
            return ToolResponse(status="error", summary=str(e))

    # ======================================================
    # SUPPORT FUNCTIONS
    # ======================================================
    def _download_pdf(self, url: str) -> Optional[bytes]:
        """Tải file PDF từ URL."""
        try:
            logger.info(f"[ToolAgent] Đang tải file PDF từ: {url}")
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoDataBot/1.0)"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower():
                logger.warning(f"[ToolAgent] Cảnh báo: Nội dung không phải PDF ({content_type})")

            return response.content
        except Exception as e:
            logger.error(f"[ToolAgent] Lỗi tải PDF từ {url}: {e}")
            return None

    async def _summarize_article(self, content: str) -> str:
        """Tóm tắt nội dung từng Điều bằng tiếng Việt."""
        try:
            prompt = ChatPromptTemplate.from_template(
                "Hãy tóm tắt ngắn gọn nội dung điều luật sau bằng tiếng Việt, chỉ giữ thông tin cốt lõi:\n\n{content}\n\n---\nTóm tắt:"
            )
            chain = prompt | self.model
            response = await chain.ainvoke({"content": content[:2500]})
            return response.content.strip()
        except Exception as e:
            logger.warning(f"[ToolAgent] Lỗi tóm tắt Điều: {e}")
            return content[:200] + "..."

    async def _summarize_whole_text(self, text: str) -> str:
        """Tóm tắt toàn văn bản luật (3–5 câu)."""
        try:
            prompt = ChatPromptTemplate.from_template(
                "Đây là một dự thảo luật của Việt Nam. Hãy tóm tắt toàn bộ nội dung văn bản bằng 3–5 câu ngắn gọn bằng tiếng Việt:\n\n{text}\n\n---\nTóm tắt:"
            )
            chain = prompt | self.model
            response = await chain.ainvoke({"text": text[:6000]})
            return response.content.strip()
        except Exception as e:
            logger.warning(f"[ToolAgent] Lỗi tóm tắt toàn văn: {e}")
            return ""

# --------------------
# WebAgent (generates BrowserAction)
# --------------------
class WebAgent(BaseAgent):
    """
    WebAgent: từ blueprint (sources) tiến hành tìm link / bài viết và crawl comment.
    Input (state/messages) có thể chứa:
      - JSON có key "sources": danh sách CrawlSource (từ BlueprintAgent)
      - Hoặc key "keywords" và "topic_summary": khi sources không có sẵn, agent tự sinh queries
    Trả về: EasyDict với 'results' (chi tiết) và 'next' (mặc định về ToolAgent)
    """

    def __init__(
        self,
        agent_name: str = "WebAgent",
        description: str = "Agent thu thập bài viết và bình luận từ các nguồn đề xuất.",
        model: Optional[object] = None,
        tools: Optional[List] = None,
        default_num_results: int = 5,
        max_comments_per_page: int = 50,
        **kwargs,
    ):
        # Không ép output_parser ở đây (WebAgent là agent thực thi), để BaseAgent xử lý chuỗi nếu cần
        instruction = load_prompt("web")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=None,
            **kwargs,
        )
        self.default_num_results = default_num_results
        self.max_comments_per_page = max_comments_per_page
        logger.info("WebAgent initialized successfully")

    # helper: parse incoming state/messages to get sources or keywords
    def _parse_input(self, state: Any) -> Dict[str, Any]:
        """
        Trả về dict có các trường:
          - sources: list[dict] (mỗi dict chứa source_name, base_url, search_query, crawl_priority, expected_data_type)
          - keywords: list[str]
          - summary: str
          - save_csv: bool, out_path: str (tuỳ chọn)
        """
        parsed = {"sources": [], "keywords": [], "summary": "", "save_csv": False, "out_path": None}
        # hỗ trợ cả AgentState (TypedDict) và raw dict
        if hasattr(state, "messages"):
            messages = state.messages
        elif isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = []

        if not messages:
            return parsed

        # Last message may contain structured JSON (BlueprintResponse) or plain text.
        last = messages[-1]
        content = getattr(last, "content", str(last)).strip()

        # Try parse JSON
        try:
            data = json.loads(content)
            # If it's blueprint-like
            if isinstance(data, dict):
                if "sources" in data and isinstance(data["sources"], list):
                    parsed["sources"] = data["sources"]
                if "keywords" in data:
                    parsed["keywords"] = data.get("keywords") or parsed["keywords"]
                if "topic_summary" in data:
                    parsed["summary"] = data.get("topic_summary") or parsed["summary"]
                # optional flags
                parsed["save_csv"] = data.get("save_csv", False)
                parsed["out_path"] = data.get("out_path")
                return parsed
            # if it's list (maybe model returned list of sources)
            if isinstance(data, list):
                parsed["sources"] = data
                return parsed
        except Exception:
            # not JSON — try to parse a fallback pattern
            pass

        # fallback: check if message contains keywords in a simple format (comma separated)
        # e.g., "keywords: khoa học, đổi mới sáng tạo"
        m = re.search(r"keywords?\s*[:\-]\s*(.+)$", content, flags=re.IGNORECASE)
        if m:
            kw_text = m.group(1)
            parsed["keywords"] = [k.strip() for k in re.split(r"[;,]", kw_text) if k.strip()]
            return parsed

        # if content is small text, set as summary
        if len(content) > 30:
            parsed["summary"] = content
            # attempt to extract keywords by simple split (if comma separated)
            if "," in content and len(content.split()) < 20:
                parsed["keywords"] = [k.strip() for k in content.split(",")][:10]

        return parsed

    # helper: find links by scanning base_url page for anchors that match keywords
    def _find_links_by_keywords(self, base_url: str, keywords: List[str], num: int) -> List[Dict[str, str]]:
        """
        Heuristic: tải base_url, tìm <a> có text/href chứa keywords. Return list of {title, link, snippet}.
        """
        html = get_page_content(base_url)
        if not html:
            return []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.find_all("a", href=True)
        candidates = []
        for a in anchors:
            href = a["href"].strip()
            title = (a.get_text(" ", strip=True) or "").strip()
            link = normalize_url(base_url, href)
            score = 0
            text_lower = title.lower()
            for kw in keywords:
                if not kw:
                    continue
                k = kw.lower()
                if k in text_lower:
                    score += 3
                if k in href.lower():
                    score += 1
            # also boost if anchor appears near "ý kiến", "bình luận", "thảo luận"
            if re.search(r"ý kiến|bình luận|thảo luận|phản hồi|góp ý", title, flags=re.IGNORECASE):
                score += 2
            if score > 0:
                snippet = None
                # try to find a short context paragraph sibling
                p = a.find_parent()
                if p:
                    snippet = p.get_text(" ", strip=True)[:300]
                candidates.append({"title": title or link, "link": link, "snippet": snippet or "" , "score": score})
        # sort by score desc, unique by link
        candidates.sort(key=lambda x: x["score"], reverse=True)
        seen = set()
        out = []
        for c in candidates:
            if c["link"] not in seen:
                seen.add(c["link"])
                out.append({"title": c["title"], "link": c["link"], "snippet": c["snippet"]})
            if len(out) >= num:
                break
        return out

    async def __call__(self, state: Any, model=None):
        """
        Entrypoint used by workflow. state contains 'messages' with blueprint or keywords.
        Returns an EasyDict with keys: messages (list), results (detailed), next (str).
        """
        try:
            parsed = self._parse_input(state)
            sources_input = parsed.get("sources", [])
            keywords = parsed.get("keywords", [])
            summary = parsed.get("summary", "")
            save_csv = parsed.get("save_csv", False)
            out_path = parsed.get("out_path", None)

            # if no sources provided by blueprint, create fallback sources from keywords
            if not sources_input and keywords:
                # create a generic source entry to search web with keywords
                q = " ".join(keywords)
                sources_input = [
                    {
                        "source_name": "web_search",
                        "base_url": "",
                        "search_query": q,
                        "crawl_priority": 3,
                        "expected_data_type": "bình luận / bài viết"
                    }
                ]

            if not sources_input:
                return EasyDict({
                    "messages": ["WebAgent: Không tìm thấy nguồn (sources) hoặc keywords để crawl."],
                    "next": "ManagerAgent",
                })

            aggregated_sources: List[Dict[str, Any]] = []
            total_links = 0
            total_comments = 0
            all_comments_rows = []  # for optional CSV export

            for src in sources_input:
                name = src.get("source_name") or src.get("name") or "unknown"
                base_url = src.get("base_url") or ""
                search_query = src.get("search_query") or ""
                num_results = int(src.get("num_results", self.default_num_results))
                priority = int(src.get("crawl_priority", 3))
                expected_type = src.get("expected_data_type", "")

                logger.info("WebAgent: processing source '%s' (query=%s)", name, search_query or base_url)

                # 1) primary: try Google CSE (search_discussions)
                links = []
                if search_query:
                    try:
                        links = search_discussions(search_query, num=num_results)
                        # transform to expected minimal structure if necessary
                        tmp = []
                        for it in links:
                            tmp.append({"title": it.get("title"), "link": it.get("link"), "snippet": it.get("snippet")})
                        links = tmp
                    except Exception as e:
                        logger.warning("WebAgent: search_discussions error: %s", e)
                        links = []

                # 2) fallback: if search returned empty and base_url available => scan base_url for keyword matches
                if not links and base_url and keywords:
                    try:
                        found = self._find_links_by_keywords(base_url, keywords, num_results)
                        links = found
                    except Exception as e:
                        logger.debug("WebAgent: fallback scan error: %s", e)
                        links = []

                # 3) fallback: if still empty and search_query present but no CSE => try simple site search by constructing site search on base_url and scraping (best-effort)
                if not links and search_query and base_url:
                    # try to hit base_url and find anchors containing any keyword tokens
                    try:
                        found = self._find_links_by_keywords(base_url, keywords or search_query.split(), num_results)
                        links = found
                    except Exception:
                        links = []

                # Now for each link, fetch page and crawl comments
                result_items: List[Dict[str, Any]] = []
                for link_obj in (links or [])[:num_results]:
                    link = link_obj.get("link")
                    title = link_obj.get("title") or ""
                    snippet = link_obj.get("snippet") or ""
                    comments = []
                    try:
                        comments = crawl_comments_from_url(link, max_items=self.max_comments_per_page)
                    except Exception as e:
                        logger.warning("WebAgent: crawl_comments_from_url failed for %s: %s", link, e)
                        comments = []

                    sample_comments = [c.get("text") for c in comments[:5]] if comments else []
                    result_items.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "comments_count": len(comments),
                        "sample_comments": sample_comments,
                    })

                    # prepare CSV rows
                    for c in comments:
                        row = {
                            "source_name": name,
                            "source_base": base_url,
                            "search_query": search_query,
                            "article_link": link,
                            "article_title": title,
                            "comment_text": c.get("text"),
                        }
                        all_comments_rows.append(row)

                    total_links += 1
                    total_comments += len(comments)

                aggregated_sources.append({
                    "source_name": name,
                    "base_url": base_url,
                    "search_query": search_query,
                    "crawl_priority": priority,
                    "expected_data_type": expected_type,
                    "results": result_items,
                })

            saved_csv_path = None
            if save_csv and out_path and all_comments_rows:
                try:
                    saved_csv_path = save_results_csv(all_comments_rows, out_path)
                except Exception as e:
                    logger.warning("WebAgent: failed to save CSV to %s: %s", out_path, e)
                    saved_csv_path = None

            response = WebAgentResponse(
                status="success",
                processed_sources=len(aggregated_sources),
                total_links_found=total_links,
                total_comments_collected=total_comments,
                sources=[SourceResult(**s) for s in aggregated_sources],
                saved_csv=saved_csv_path,
            )

            # Return in same style as other ToolAgent returns (EasyDict)
            return EasyDict({
                "messages": [f"WebAgent: processed {len(aggregated_sources)} sources, collected {total_comments} comments."],
                "results": response,
                "next": "ToolAgent",
            })

        except Exception as e:
            logger.error("WebAgent encountered error: %s", e)
            return EasyDict({
                "messages": [f"WebAgent error: {e}"],
                "next": "ManagerAgent",
            })
# ======================================================
# BLUEPRINT AGENT
# ======================================================
class BlueprintAgent(BaseAgent):
    """
    BlueprintAgent — tạo kế hoạch crawl dữ liệu dư luận về dự thảo luật,
    bao gồm danh sách nguồn, từ khóa tìm kiếm và độ ưu tiên crawl.
    """

    def __init__(
        self,
        agent_name: str = "BlueprintAgent",
        description: str = "Agent có nhiệm vụ xây dựng bản thiết kế (blueprint) dữ liệu, xác định cấu trúc dữ liệu cần trích xuất và định dạng lưu trữ.",
        model=None,
        tools=None,
        output_parser=None,
        **kwargs,
    ):
        # 🔹 Load prompt blueprint.md
        instruction = load_prompt("blueprint")

        super().__init__(
            agent_name=agent_name,
            instruction=instruction,  # ⚠️ dòng bắt buộc
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
            **kwargs,
        )
        logger.info("BlueprintAgent initialized successfully")
    # ======================================================
    # MAIN FUNCTION
    # ======================================================
    async def run(self, input_data: Dict[str, Any]) -> BlueprintResponse:
        """
        input_data example:
        {
            "summary": "...",
            "keywords": ["đổi mới sáng tạo", "nghiên cứu khoa học", "công nghệ", ...]
        }
        """
        try:
            logger.info("[BlueprintAgent] Bắt đầu sinh kế hoạch crawl...")

            summary = input_data.get("summary", "")
            keywords = input_data.get("keywords", [])

            if not summary and not keywords:
                raise ValueError("Thiếu dữ liệu đầu vào cho BlueprintAgent")

            # Dùng LLM để sinh danh sách nguồn crawl
            sources = await self._generate_crawl_blueprint(summary, keywords)

            return BlueprintResponse(
                status="success",
                topic_summary=summary,
                keywords=keywords,
                sources=sources,
                total_sources=len(sources),
            )

        except Exception as e:
            logger.error(f"[BlueprintAgent] Lỗi khi sinh kế hoạch crawl: {e}")
            return BlueprintResponse(status="error", topic_summary=str(e))

    # ======================================================
    # SUPPORT FUNCTIONS
    # ======================================================
    async def _generate_crawl_blueprint(
        self, summary: str, keywords: List[str]
    ) -> List[CrawlSource]:
        """Dùng mô hình Ollama để đề xuất danh sách nguồn và truy vấn crawl."""
        try:
            prompt = ChatPromptTemplate.from_template(
                """
                Bạn là chuyên gia thu thập dữ liệu trực tuyến. 
                Cho nội dung tóm tắt sau đây về một **dự thảo luật của Việt Nam**, 
                hãy tạo danh sách 8–12 nguồn web tiềm năng để crawl thông tin, bao gồm:
                - Các trang báo chính thống (vnexpress, dantri, baochinhphu, vov, cafef)
                - Các diễn đàn, mạng xã hội (facebook, reddit, tiktok, youtube)
                - Các cổng góp ý dự thảo (duthaoonline.quochoi.vn, mst.gov.vn)

                Dữ liệu đầu vào:
                - Tóm tắt: {summary}
                - Từ khóa: {keywords}

                Đầu ra yêu cầu:
                JSON gồm danh sách các đối tượng với trường:
                {{
                    "source_name": "...",
                    "base_url": "...",
                    "search_query": "...",
                    "crawl_priority": 1-5,
                    "expected_data_type": "..."
                }}
                """
            )

            chain = prompt | self.model
            response = await chain.ainvoke({
                "summary": summary,
                "keywords": ", ".join(keywords),
            })

            # Phân tích kết quả JSON từ mô hình
            import json
            try:
                sources_json = json.loads(response.content)
                sources = [CrawlSource(**src) for src in sources_json if isinstance(src, dict)]
                return sources
            except Exception:
                # Fallback: xử lý chuỗi trả về không chuẩn
                logger.warning("[BlueprintAgent] Phản hồi không phải JSON hợp lệ, fallback sang heuristic parse.")
                sources = []
                lines = response.content.split("\n")
                for line in lines:
                    if "http" in line:
                        parts = line.split("-")
                        name = parts[0].strip()
                        url = [w for w in parts if "http" in w]
                        sources.append(
                            CrawlSource(
                                source_name=name,
                                base_url=url[0] if url else "",
                                search_query=f"ý kiến về {', '.join(keywords)} site:{url[0] if url else 'vnexpress.net'}",
                                crawl_priority=3,
                                expected_data_type="bài viết"
                            )
                        )
                return sources

        except Exception as e:
            logger.error(f"[BlueprintAgent] Lỗi sinh danh sách nguồn crawl: {e}")
            return []




RESEARCH_AGENTS = [PlannerAgent.__name__, WebAgent.__name__, BlueprintAgent.__name__]
