import sys
import os
from typing import Callable, Optional, List
from pydantic import BaseModel,Field
from autodata.agents.base import BaseAgent, BaseResponse
import logging

sys.dont_write_bytecode = True

from autodata.agents.base import BaseAgent
from autodata.prompts.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


class EngineerResponse(BaseResponse):
    thought: str = Field(..., description="Reasoning or assumptions about the implementation")
    dependencies: List[str] = Field(..., description="List of required Python packages")
    code: str = Field(..., description="The complete Python source code")
    explanation: str = Field(..., description="Explanation of how the code works and how to run it")

class EngineerAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "EngineerAgent",
        description: str = "A code agent that writes code.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):

        instruction = load_prompt("engineer")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=EngineerResponse,
        )
        logger.info("EngineerAgent initialized successfully")


class TestAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "TestAgent",
        description: str = "A test agent that tests the code.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("test")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("TestAgent initialized successfully")

class ValidationResponse(BaseResponse):
    status: str = Field(description="Validation status: success or failed")
    summary: str = Field(description="Summary of validation results")
    issues: list[dict] = Field(description="List of validation issues if any")

class ValidationAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "ValidationAgent",
        description: str = "A validation agent that validates the code.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("valid")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=ValidationResponse,
        )
        logger.info("ValidationAgent initialized successfully")


DEVELOPMENT_AGENTS = [
    EngineerAgent.__name__,
    TestAgent.__name__,
    ValidationAgent.__name__,
]
