import sys
import os
from pathlib import Path
from typing import Optional
import logging
from langchain_core.messages import HumanMessage
#from langchain_google_genai import GoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

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
        """Initialize AutoData with configuration and logging setup.

        Args:
            config_path: Optional path to configuration file
            log_level: Logging level (default: "INFO")
            output_dir: Optional output directory for results
            verbose: Enable verbose output
            env_path: Optional path to .env file for API keys and environment variables
        """
        # Setup logging first
        setup_logging(log_level)

        # Load environment variables
        load_environment_variables_from_file(env_path)

        # Initialize configuration
        self.config = (
            AutoDataConfig.from_file(config_path) if config_path else AutoDataConfig()
        )
        self.output_dir = output_dir
        self.verbose = verbose

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Initialize agents
        self.manager = ManagerAgent(model=self.llm)
        self.planner = PlannerAgent(model=self.llm)
        self.tools = ToolAgent(model=self.llm)
        self.browser = WebAgent(model=self.llm)
        self.blueprint = BlueprintAgent(model=self.llm)
        self.engineer = EngineerAgent(model=self.llm)
        self.test = TestAgent(model=self.llm)
        self.validator = ValidationAgent(model=self.llm)

        # Build workflow
        workflow = self._build_workflow()
        self.workflow = workflow.compile()

    def _initialize_llm(self):
        """Initialize the language model with proper configuration."""
        try:
            llm = globals()[self.config.LLM_Config.ModelClass](
                **self.config.LLM_Config._get_additional_kwargs()
            )
            logger.info(f"✅ Initialized LLM: {self.config.LLM_Config.ModelClass}")
            return llm
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            logger.info("💡 Falling back to GoogleGenerativeAI with JSON-enforced configuration")

            # Fallback to default GoogleGenerativeAI (fixed version)
            return ChatGoogleGenerativeAI(
                model=self.config.LLM_Config.model,
                temperature=self.config.LLM_Config.temperature,
                max_output_tokens=self.config.LLM_Config.max_tokens,
                google_api_key=( self.config.LLM_Config.api_key or os.getenv("GOOGLE_API_KEY") ),
                convert_system_message_to_human=True,  # ✅ giúp Gemini hiểu system prompt

            )

    def _build_workflow(self):
        """Build the multi-agent workflow graph."""
        try:
            graph = StateGraph(AgentState)

            # Add nodes
            graph.add_node("ManagerAgent", self.manager)
            graph.add_node("PlannerAgent", self.planner)
            graph.add_node("WebAgent", self.browser)
            graph.add_node("ToolAgent", self.tools)
            graph.add_node("BlueprintAgent", self.blueprint)
            graph.add_node("EngineerAgent", self.engineer)
            graph.add_node("TestAgent", self.test)
            graph.add_node("ValidationAgent", self.validator)

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

            # Kết thúc
            graph.add_edge("ManagerAgent", END)

            # Add conditional routing from manager
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
                    "[END]": END,
                },
            )

            logger.info("✅ Workflow graph built successfully")
            return graph

        except Exception as e:
            logger.error(f"❌ Failed to build workflow: {e}")
            return None

    async def arun(self, instruction: str):
        """Run the AutoData system with the given instruction.

        Args:
            instruction: User instruction for data collection

        Returns:
            dict: Results of the data collection process
        """
        try:
            logger.info(
                f"🚀 Starting AutoData workflow with instruction: {instruction}"
            )

            input_state = AgentState(
                messages=[HumanMessage(content=instruction)],
                sender="START",
                next="ManagerAgent",
            )

            async for update in self.workflow.astream(input_state):
                logger.info(f"🔄 Workflow update: {update}")

        except Exception as e:
            import traceback
            logger.error(f"❌ AutoData workflow failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "instruction": instruction,
            }

