import sys
import os
from typing import Callable, Optional, List
from pydantic import BaseModel, Field
import logging
from easydict import EasyDict

sys.dont_write_bytecode = True

from autodata.core.types import AgentState
from autodata.agents.base import BaseAgent, BaseResponse
from autodata.prompts.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


class Step(BaseResponse):
    name: str = Field(description="The name of the step.")
    description: str = Field(description="The description of the step.")
    output: str = Field(description="The expected output of the step.")


class PlannerResponse(BaseResponse):
    thought: str = Field(description="A thinking step to complete the given user task.")
    steps: List[Step] = Field(
        description="A list of detailed steps to complete the task."
    )


class PlannerAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "PlannerAgent",
        description: str = "A planner agent to plan the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = PlannerResponse,
        **kwargs,
    ):
        instruction = load_prompt("planner")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )

        logger.info("PlannerAgent initialized successfully")


class ToolAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "ToolAgent",
        description: str = "A tool agent to use tools for the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("tool")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("ToolAgent initialized successfully")

    async def __call__(self, state: AgentState, llm=None):
        assert llm or self._model, "Please provide valid LLM."
        llm = llm if llm is not None else self._model

        response = self.llm.ainvoke(state)
        tool_calls = response.tool_calls
        tool_call = tool_calls[0]
        tool_name = tool_call["name"]
        tool_func = globals()[tool_name](config=self.config)
        response = await tool_func.ainvoke(tool_call)
        return EasyDict({"messages": [response]})


class WebResponse(BaseResponse):
    pass


class BlueprintAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "BlueprintAgent",
        description: str = "A blueprint agent to create a development blueprint for the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("blueprint")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("BlueprintAgent initialized successfully")


class WebAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "WebAgent",
        description: str = "A web agent to search the web for the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("browser")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("WebAgent initialized successfully")


RESEARCH_AGENTS = [
    PlannerAgent.__name__,
    WebAgent.__name__,
    BlueprintAgent.__name__,
]
