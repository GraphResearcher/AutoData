"""
Main entry point for the AutoData package.

This module implements the core workflow of the multi-agent system for automated web data collection.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from autodata.agents.research import PlannerAgent, WebAgent, ToolAgent, BlueprintAgent
from autodata.agents.development import EngineerAgent, TestAgent, ValidationAgent
from autodata.agents.manager import ManagerAgent
from autodata.core.config import AutoDataConfig
from autodata.core.types import AgentState
from autodata.utils.logging import setup_logging

logger = logging.getLogger(__name__)


class AutoData:
    """Main class for the AutoData package."""

    def __init__(self, config_path: Optional[Path] = None, log_level: str = "INFO"):
        """Initialize AutoData with configuration and logging setup.

        Args:
            config_path: Optional path to configuration file
            log_level: Logging level (default: "INFO")
        """
        setup_logging(log_level)
        self.config = (
            AutoDataConfig.from_file(config_path) if config_path else AutoDataConfig()
        )

        # Initialize agents
        self.manager = ManagerAgent(self.config)
        self.planner = PlannerAgent(self.config)
        self.web_agent = WebAgent(self.config)
        self.tool_agent = ToolAgent(self.config)
        self.blueprint_agent = BlueprintAgent(self.config)
        self.engineer = EngineerAgent(self.config)
        self.tester = TestAgent(self.config)
        self.validator = ValidationAgent(self.config)

        # Initialize tool executor
        self.tool_executor = ToolExecutor(self._get_tools())

        # Build the agent graph
        self.workflow = self._build_workflow()

    def _get_tools(self) -> Dict[str, Any]:
        """Get the tools available to agents."""
        return {
            "web_browse": self.web_agent.browse,
            "search": self.tool_agent.search,
            "execute_code": self.engineer.execute_code,
            "validate_data": self.validator.validate,
        }

    def _build_workflow(self) -> StateGraph:
        """Build the agent workflow graph."""
        workflow = StateGraph(AgentState)

        # Add nodes for each agent
        workflow.add_node("manager", self.manager.run)
        workflow.add_node("planner", self.planner.run)
        workflow.add_node("web_agent", self.web_agent.run)
        workflow.add_node("tool_agent", self.tool_agent.run)
        workflow.add_node("blueprint_agent", self.blueprint_agent.run)
        workflow.add_node("engineer", self.engineer.run)
        workflow.add_node("tester", self.tester.run)
        workflow.add_node("validator", self.validator.run)

        # Define edges and routing logic
        workflow.add_edge("manager", "planner")
        workflow.add_conditional_edges(
            "planner",
            self._route_research_tasks,
            {
                "web_agent": "web_agent",
                "tool_agent": "tool_agent",
                "blueprint_agent": "blueprint_agent",
                "end_research": "engineer",
            },
        )
        workflow.add_edge("web_agent", "planner")
        workflow.add_edge("tool_agent", "planner")
        workflow.add_edge("blueprint_agent", "engineer")
        workflow.add_edge("engineer", "tester")
        workflow.add_conditional_edges(
            "tester",
            self._route_test_results,
            {"retry": "engineer", "validate": "validator"},
        )
        workflow.add_conditional_edges(
            "validator",
            self._route_validation_results,
            {"retry": "engineer", "complete": END},
        )

        # Set entry point
        workflow.set_entry_point("manager")

        return workflow.compile()

    def _route_research_tasks(self, state: AgentState) -> str:
        """Route research tasks to appropriate agents."""
        if state.get("research_complete", False):
            return "end_research"
        return state.get("next_agent", "planner")

    def _route_test_results(self, state: AgentState) -> str:
        """Route test results to next step."""
        if state.get("test_passed", False):
            return "validate"
        return "retry"

    def _route_validation_results(self, state: AgentState) -> str:
        """Route validation results to next step."""
        if state.get("validation_passed", False):
            return "complete"
        return "retry"

    def run(self, user_instruction: str) -> Dict[str, Any]:
        """Run the AutoData workflow with the given user instruction.

        Args:
            user_instruction: The user's data collection instruction

        Returns:
            Dict containing the results and metadata
        """
        try:
            # Initialize state
            initial_state = AgentState(
                user_instruction=user_instruction,
                messages=[],
                research_results={},
                blueprint=None,
                code=None,
                test_results=None,
                validation_results=None,
            )

            # Run the workflow
            final_state = self.workflow.invoke(initial_state)

            return {
                "status": "success",
                "results": final_state.get("validation_results"),
                "metadata": {
                    "research_results": final_state.get("research_results"),
                    "blueprint": final_state.get("blueprint"),
                    "code": final_state.get("code"),
                    "test_results": final_state.get("test_results"),
                },
            }

        except Exception as e:
            logger.error(f"Error running AutoData workflow: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}


def main():
    """Main entry point for the AutoData CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AutoData - Automated Web Data Collection"
    )
    parser.add_argument("instruction", help="User instruction for data collection")
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    autodata = AutoData(config_path=args.config, log_level=args.log_level)
    results = autodata.run(args.instruction)

    if results["status"] == "success":
        print("Data collection completed successfully!")
        print("\nResults:")
        print(results["results"])
    else:
        print(f"Error: {results['error']}")


if __name__ == "__main__":
    main()
