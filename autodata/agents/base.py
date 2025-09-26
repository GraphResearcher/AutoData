"""
Base agent class for the AutoData package.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

from pydantic import BaseModel
from easydict import EasyDict
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from autodata.core.types import AgentState


class BaseResponse(BaseModel):

    def to_easydict(self):
        return EasyDict(self.model_dump())

    def to_dict(self):
        return self.model_dump()

    def to_message(self):
        return str(self.to_dict())


class BaseAgent:
    """Base class for all agents in the system.

    Attributes:
        instruction (str): The instruction text for the agent
        description (str): A description of the agent's purpose
        model (str): The language model to use
        output_parser (BaseModel): Parser for agent outputs
        agent_name (str): Unique identifier for the agent
        config (Optional[Dict | EasyDict]): Configuration parameters
        tools (List[Callable]): List of available tools
    """

    def __init__(
        self,
        instruction: str, ## hướng dẫn (system message) cho agent.
        description: str, #mô tả agent dùng để làm gì.
        model: Optional[str] = None,
        output_parser: Optional[BaseModel] = None, #parser để parse output theo schema Pydantic.
        agent_name: str = None,
        config: Optional[Dict | EasyDict] = None,
        tools: Optional[List[Callable]] = None,
    ) -> None:
        """Initialize the base agent.

        Args:
            instruction: The instruction text for the agent
            description: A description of the agent's purpose
            model: The language model to use
            output_parser: Parser for agent outputs
            agent_name: Unique identifier for the agent
            config: Configuration parameters
            tools: List of available tools
        """
        self._model = model
        self._instruction = instruction
        self._description = description
        self._agent_name = agent_name
        self._config = EasyDict(config) if not isinstance(config, EasyDict) else config
        self._tools = tools

        self._output_parser = output_parser
        self._parser = PydanticOutputParser(pydantic_object=output_parser)

        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    " You are a helpful AI assistant, collaborating with other assistants."
                    " Remember to focus on your given task only, do not do another assistant work ."
                    " \n{system_message}"
                    " \n{format_instructions}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            system_message=self._instruction,
            format_instructions=(
                self._parser.get_format_instructions() if self._output_parser else ""
            ),
        )

    async def __call__(self, state: AgentState, model=None):
        assert model or self._model, "Please provide valid LLM."
        llm = model if model is not None else self._model

        if self._tools:
            llm = llm.bind_tools(self._tools)

        parser = self._parser
        prompt = self._prompt

        chain = prompt | llm | parser

        response = chain.invoke(state)

        output = EasyDict(
            {
                "messages": [
                    HumanMessage(content=response.to_message(), name=self._agent_name),
                ],
            }
        )
        return output
