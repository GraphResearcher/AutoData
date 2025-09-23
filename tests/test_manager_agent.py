"""Tests for ManagerAgent."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage

from autodata.agents.manager import ManagerAgent, ManagerResponse
from autodata.core.config import AutoDataConfig
from autodata.core.types import AgentState


class TestManagerAgent:
    """Test cases for ManagerAgent."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = AutoDataConfig()
        config.llm.api_key = "test_key"
        return config

    @pytest.fixture
    def agent_state(self):
        """Create a test agent state."""
        return AgentState(
            sender="TestSender",
            next="ManagerAgent",
            messages=[HumanMessage(content="Test message", name="TestAgent")],
        )

    def test_manager_agent_initialization(self, config):
        """Test ManagerAgent initialization."""
        agent = ManagerAgent(config)

        assert agent.config == config
        assert agent._agent_name == "ManagerAgent"
        assert "PlannerAgent" in agent.worker_names
        assert "WebAgent" in agent.worker_names
        assert "ValidationAgent" in agent.worker_names
        assert len(agent.worker_names) == 7

    def test_manager_agent_initialization_with_model(self, config):
        """Test ManagerAgent initialization with custom model."""
        mock_model = Mock()
        agent = ManagerAgent(config, model=mock_model)

        assert agent.config == config
        assert agent._model == mock_model
        assert agent._agent_name == "ManagerAgent"

    def test_manager_response_model(self):
        """Test ManagerResponse model."""
        response = ManagerResponse(
            message="Test command",
            next_agent="PlannerAgent",
            status="planning",
            reasoning="Starting the workflow",
        )

        assert response.message == "Test command"
        assert response.next_agent == "PlannerAgent"
        assert response.status == "planning"
        assert response.reasoning == "Starting the workflow"

    def test_determine_next_agent_planning(self, config):
        """Test determine_next_agent for planning stage."""
        agent = ManagerAgent(config)

        next_agent = agent.determine_next_agent("initial", "planning")
        assert next_agent == "PlannerAgent"

    def test_determine_next_agent_research(self, config):
        """Test determine_next_agent for research stage."""
        agent = ManagerAgent(config)

        # Test web browsing needed
        next_agent = agent.determine_next_agent("web_browsing_needed", "research")
        assert next_agent == "WebAgent"

        # Test tool search needed
        next_agent = agent.determine_next_agent("tool_search_needed", "research")
        assert next_agent == "ToolAgent"

        # Test default research
        next_agent = agent.determine_next_agent("other", "research")
        assert next_agent == "BlueprintAgent"

    def test_determine_next_agent_development(self, config):
        """Test determine_next_agent for development stage."""
        agent = ManagerAgent(config)

        # Test coding needed
        next_agent = agent.determine_next_agent("coding_needed", "development")
        assert next_agent == "EngineerAgent"

        # Test testing needed
        next_agent = agent.determine_next_agent("testing_needed", "development")
        assert next_agent == "TestAgent"

        # Test default development
        next_agent = agent.determine_next_agent("other", "development")
        assert next_agent == "ValidationAgent"

    def test_assess_workflow_progress_empty(self, config, agent_state):
        """Test assess_workflow_progress with empty state."""
        agent = ManagerAgent(config)

        # Empty state
        empty_state = AgentState(sender="", next="", messages=[])
        assessment = agent.assess_workflow_progress(empty_state)

        assert assessment["completed_stages"] == []
        assert assessment["current_stage"] == "planning"

    def test_assess_workflow_progress_with_messages(self, config):
        """Test assess_workflow_progress with various agent messages."""
        agent = ManagerAgent(config)

        # State with planner message
        state_with_planner = AgentState(
            sender="PlannerAgent",
            next="WebAgent",
            messages=[HumanMessage(content="Plan created", name="PlannerAgent")],
        )

        assessment = agent.assess_workflow_progress(state_with_planner)
        assert "planning" in assessment["completed_stages"]
        assert assessment["current_stage"] == "research"

    @pytest.mark.asyncio
    async def test_run_error_handling(self, config, agent_state):
        """Test error handling in run method."""
        agent = ManagerAgent(config)

        # Mock the base agent call to raise an exception
        with patch.object(agent, "__call__", side_effect=Exception("Test error")):
            result = await agent.run(agent_state)

            assert result["sender"] == "ManagerAgent"
            assert len(result["messages"]) > len(agent_state["messages"])

            # Check that error message was added
            error_message = result["messages"][-1]
            assert "ManagerAgent encountered an error" in error_message.content

    @patch("src.autodata.prompts.prompt_loader.load_prompt")
    def test_prompt_loading(self, mock_load_prompt, config):
        """Test that prompt is loaded correctly."""
        mock_load_prompt.return_value = "Mock prompt"

        agent = ManagerAgent(config)

        # Verify load_prompt was called with correct parameters
        mock_load_prompt.assert_called_once_with(
            "manager", WORKER_NAMES=agent.worker_names
        )
        assert agent._instruction == "Mock prompt"

    def test_manager_response_to_dict(self):
        """Test ManagerResponse serialization."""
        response = ManagerResponse(
            message="Test command",
            next_agent="PlannerAgent",
            status="planning",
            reasoning="Starting the workflow",
        )

        response_dict = response.to_dict()

        assert response_dict["message"] == "Test command"
        assert response_dict["next_agent"] == "PlannerAgent"
        assert response_dict["status"] == "planning"
        assert response_dict["reasoning"] == "Starting the workflow"

    def test_manager_response_to_easydict(self):
        """Test ManagerResponse EasyDict conversion."""
        response = ManagerResponse(
            message="Test command",
            next_agent="PlannerAgent",
            status="planning",
            reasoning="Starting the workflow",
        )

        easy_dict = response.to_easydict()

        assert easy_dict.message == "Test command"
        assert easy_dict.next_agent == "PlannerAgent"
        assert easy_dict.status == "planning"
        assert easy_dict.reasoning == "Starting the workflow"
