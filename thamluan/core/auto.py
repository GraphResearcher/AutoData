"""
Auto.py - Setup LangGraph workflow với nodes và edges (Async only).
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from core.types import AgentState, TaskType, create_initial_state
from agents import (
    manager_agent,
    web_crawler_agent,
    pdf_handler_agent,
    content_extractor_agent,
    search_agent,
    article_analyzer_agent,
    exporter_agent,
    legal_pdf_search_agent
)

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """Tạo LangGraph workflow cho AutoData system (async agents)."""
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("manager", manager_agent.execute)
    workflow.add_node("legal_pdf_search", legal_pdf_search_agent.execute)
    workflow.add_node("web_crawler", web_crawler_agent.execute)
    workflow.add_node("pdf_handler", pdf_handler_agent.execute)
    workflow.add_node("content_extractor", content_extractor_agent.execute)
    workflow.add_node("search_agent", search_agent.execute)
    workflow.add_node("article_analyzer", article_analyzer_agent.execute)
    workflow.add_node("exporter_agent", exporter_agent.execute)

    # Routing từ manager dựa vào task hiện tại
    def route_from_manager(state: AgentState) -> str:
        current_task = state.get('current_task')
        is_complete = state.get('is_complete', False)

        logger.info(
            f"🔀 Routing: current_task={current_task.task_type.value if current_task else 'None'}, is_complete={is_complete}")

        if not current_task:
            logger.info("❌ No current task, ending workflow")
            return END

        if is_complete:
            logger.info(" Workflow marked as complete, ending")
            return END

        task_type = current_task.task_type
        next_agent = {
            TaskType.SEARCH_PDF_BY_KEYWORDS: "legal_pdf_search",
            TaskType.CRAWL_WEB: "web_crawler",
            TaskType.DOWNLOAD_PDF: "pdf_handler",
            TaskType.EXTRACT_CONTENT: "content_extractor",
            TaskType.SEARCH_OPINIONS: "search_agent",
            TaskType.SCRAPE_ARTICLES: "article_analyzer",
            TaskType.EXPORT_DATA: "exporter_agent"
        }.get(task_type, END)

        logger.info(f" Routing to: {next_agent}")
        return next_agent

    # Check workflow continue
    def should_continue(state: AgentState) -> str:
        if state.get('is_complete') or len(state.get('errors', [])) > 5:
            return END
        return "manager"

    # Entry point
    workflow.set_entry_point("manager")

    # Edges
    workflow.add_conditional_edges(
        "manager",
        route_from_manager,
        {
            "legal_pdf_search": "legal_pdf_search",
            "web_crawler": "web_crawler",
            "pdf_handler": "pdf_handler",
            "content_extractor": "content_extractor",
            "search_agent": "search_agent",
            "article_analyzer": "article_analyzer",
            "exporter_agent": "exporter_agent",
            END: END
        }
    )

    for node in ["legal_pdf_search", "web_crawler", "pdf_handler", "content_extractor",
                 "search_agent", "article_analyzer", "exporter_agent"]:
        workflow.add_conditional_edges(node, should_continue)

    return workflow


async def run_workflow_async(project_name: str, target_url: str = None, keywords: str = None) -> Dict[str, Any]:
    """
    Chạy workflow bất đồng bộ với keywords hoặc target URL.
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting AutoData Workflow (Async)")
        logger.info("=" * 80)
        logger.info(f"Project: {project_name}")
        if keywords:
            logger.info(f"Keywords: {keywords}")
        if target_url:
            logger.info(f"Target URL: {target_url}")
        logger.info("=" * 80)

        initial_state = create_initial_state(project_name, target_url=target_url, keywords=keywords)
        workflow = create_workflow()
        app = workflow.compile(
            checkpointer=None,
            interrupt_before=None,
            interrupt_after=None,
            debug=False
        )
        # Configure with higher recursion limit
        config = {"recursion_limit": 100}

        logger.info("🚀 Executing workflow asynchronously...")
        final_state = await app.ainvoke(initial_state, config=config)

        report = manager_agent.generate_report(final_state)
        logger.info("=" * 80)
        logger.info("Workflow Report")
        logger.info("=" * 80)
        for key, value in report.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 80)

        return final_state

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        raise


# Export
__all__ = ["create_workflow", "run_workflow_async"]
