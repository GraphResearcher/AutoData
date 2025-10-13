import sys
import os
from pathlib import Path
from typing import Optional
import logging
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

sys.dont_write_bytecode = True

from autodata.core.types import AgentState
from autodata.agents.res import PlannerAgent, WebAgent, BlueprintAgent, ToolAgent
from autodata.agents.dev import EngineerAgent, TestAgent, ValidationAgent
from autodata.agents.manager import ManagerAgent
from autodata.utils.logging import setup_logging
from autodata.core.config import AutoDataConfig, load_environment_variables_from_file

logger = logging.getLogger(__name__)


class AutoData:
    def __init__(
        self,
        config_path: Optional[Path] = None,
        log_level: str = "INFO",
        output_dir: Optional[Path] = None,
        verbose: bool = False,
        env_path: Optional[Path] = None,
    ):
        """Initialize AutoData with configuration and logging setup."""
        setup_logging(log_level)
        load_environment_variables_from_file(env_path)

        # Load configuration
        self.config = (
            AutoDataConfig.from_file(config_path)
            if config_path
            else AutoDataConfig()
        )
        self.output_dir = output_dir
        self.verbose = verbose

        # Initialize Ollama model
        self.llm = self._initialize_llm()

        # Initialize all agents
        self.manager = ManagerAgent(model=self.llm)
        self.planner = PlannerAgent(model=self.llm)
        self.tools = ToolAgent(model=self.llm)
        self.browser = WebAgent(model=self.llm)
        self.blueprint = BlueprintAgent(model=self.llm)
        self.engineer = EngineerAgent(model=self.llm)
        self.test = TestAgent(model=self.llm)
        self.validator = ValidationAgent(model=self.llm)

        # Build and compile workflow graph
        workflow = self._build_workflow()
        self.workflow = workflow.compile()

    def _initialize_llm(self):
        """Initialize Ollama model from configuration."""
        try:
            llm = ChatOllama(
                model=self.config.LLM_Config.model or "llama3.1:8b",
                temperature=self.config.LLM_Config.temperature or 0.3,
                num_ctx=self.config.LLM_Config.num_ctx or 4096,
                base_url=self.config.LLM_Config.base_url
                or "http://localhost:11434",
            )
            logger.info(f"Initialized Ollama LLM: {self.config.LLM_Config.model}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}")
            raise

    def _build_workflow(self):
        """Build the multi-agent workflow graph."""
        try:
            # 👇 Thêm concurrency="sequential" để tránh lỗi song song next
            graph = StateGraph(AgentState, concurrency="sequential")

            # Add nodes
            graph.add_node("ManagerAgent", self.manager)
            graph.add_node("PlannerAgent", self.planner)
            graph.add_node("WebAgent", self.browser)
            graph.add_node("ToolAgent", self.tools)
            graph.add_node("BlueprintAgent", self.blueprint)
            graph.add_node("EngineerAgent", self.engineer)
            graph.add_node("TestAgent", self.test)
            graph.add_node("ValidationAgent", self.validator)

            # Define workflow sequence
            graph.add_edge(START, "ManagerAgent")

            # Step 1 — Research Squad
            graph.add_edge("ManagerAgent", "PlannerAgent")
            graph.add_edge("PlannerAgent", "WebAgent")
            graph.add_edge("WebAgent", "ToolAgent")
            graph.add_edge("ToolAgent", "BlueprintAgent")
            graph.add_edge("BlueprintAgent", "ManagerAgent")

            # Step 2 — Develop Squad
            graph.add_edge("ManagerAgent", "EngineerAgent")
            graph.add_edge("EngineerAgent", "TestAgent")
            graph.add_edge("TestAgent", "ValidationAgent")
            graph.add_edge("ValidationAgent", "ManagerAgent")

            # End workflow
            graph.add_edge("ManagerAgent", END)

            # Conditional routing
            graph.add_conditional_edges(
                "ManagerAgent",
                lambda x: x["next"],
                {
                    "PlannerAgent": "PlannerAgent",
                    "WebAgent": "WebAgent",
                    "BlueprintAgent": "BlueprintAgent",
                    "ToolAgent": "ToolAgent",
                    "EngineerAgent": "EngineerAgent",
                    "TestAgent": "TestAgent",
                    "ValidationAgent": "ValidationAgent",
                    "ManagerAgent": "ManagerAgent",
                    "[END]": END,
                },
            )

            logger.info("Workflow graph built successfully")
            return graph

        except Exception as e:
            logger.error(f"Failed to build workflow: {e}")
            return None

    async def arun(self, instruction: str):
        """Run the AutoData system asynchronously with the given instruction."""
        try:
            logger.info(f"Starting AutoData workflow with instruction: {instruction}")

            input_state = AgentState(
                messages=[HumanMessage(content=instruction)],
                sender="START",
                next="ManagerAgent",
            )

            async for update in self.workflow.astream(input_state):
                logger.info(f"Workflow update: {update}")

        except Exception as e:
            import traceback

            logger.error(f"AutoData workflow failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "instruction": instruction,
            }
