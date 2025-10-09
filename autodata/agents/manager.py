import sys
import os
import logging
from typing import Dict, List, Optional, Callable, Any
from easydict import EasyDict
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

sys.dont_write_bytecode = True

from autodata.agents.base import BaseResponse, BaseAgent
from autodata.agents.res import RESEARCH_AGENTS
from autodata.agents.dev import DEVELOPMENT_AGENTS
from autodata.core.config import AutoDataConfig
from autodata.core.types import AgentState
from autodata.prompts.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


class ManagerResponse(BaseResponse):
    """
    Response from the manager agent.
    """

    message: str = Field(description="The command you need to pass to the next agent.")
    next: str = Field(description="The name of the next agent to handle the task.")
    status: str = Field(description="Current status of the workflow.")
    reasoning: str = Field(description="Reasoning behind the decision.")


class ManagerAgent(BaseAgent):
    """
    Manager agent responsible for coordinating multiple agents to collect data.

    The manager agent oversees the multi-agent workflow, coordinates between
    research and development groups, and ensures the data collection process
    follows the defined workflow.
    """

    def __init__(
        self,
        agent_name: str = "ManagerAgent",
        description: str = "A manager agent to manage the task process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: BaseModel = ManagerResponse,
        **kwargs,
    ):
        """Initialize the ManagerAgent.

        Args:
            config: AutoDataConfig instance containing LLM and other settings
            description: Description of the agent's purpose
            model: Optional LLM model instance, if None will use model from config
            output_parser: Parser for agent outputs
        """

        # Load the manager prompt template with worker names
        instruction = load_prompt(
            "manager", WORKER_NAMES=RESEARCH_AGENTS + DEVELOPMENT_AGENTS
        )

        # Initialize the base agent
        super().__init__(
            instruction=instruction,
            description=description,
            model=model,
            output_parser=output_parser,
            agent_name=agent_name,
            tools=tools,
        )

        logger.info("ManagerAgent initialized successfully")

    async def __call__(self, state: AgentState, model=None):
        assert model or self._model, "Please provide valid LLM."
        llm = model if model is not None else self._model

        output_format = self._output_parser
        prompt = self._prompt

        chain = prompt | llm.with_structured_output(output_format)
        response = chain.invoke(state)

        # Chuẩn hóa hướng đi tiếp theo
        next_agent = response.next.strip() if response.next else ""

        # ✅ Nếu manager kết thúc workflow, gán [END]
        if any(word in next_agent.lower() for word in ["user", "done", "complete", "finish", "end"]):
            next_agent = "[END]"

        message_to_return = EasyDict(
            next=next_agent,
            messages=[response.message]
        )

        return message_to_return

