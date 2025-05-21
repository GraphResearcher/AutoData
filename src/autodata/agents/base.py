"""
Base agent class for the AutoData package.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from autodata.core.config import AutoDataConfig
from autodata.core.types import AgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the AutoData system."""

    def __init__(self, config: AutoDataConfig):
        """Initialize the agent with configuration.

        Args:
            config: AutoData configuration object
        """
        self.config = config
        self.llm = ChatOpenAI(
            model_name=config.llm.model_name,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            api_key=config.llm.api_key,
        )

    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        """Run the agent's main logic.

        Args:
            state: Current state of the workflow

        Returns:
            Updated state
        """
        pass

    def _add_message(
        self, state: AgentState, content: str, role: str = "assistant"
    ) -> None:
        """Add a message to the state's message history.

        Args:
            state: Current state
            content: Message content
            role: Message role ("human" or "assistant")
        """
        if role == "human":
            message = HumanMessage(content=content)
        else:
            message = AIMessage(content=content)
        state.messages.append(message)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        return f"You are an AI agent in the AutoData system. Your role is {self.__class__.__name__}."

    def _get_chat_history(self, state: AgentState) -> List[BaseMessage]:
        """Get the chat history for this agent.

        Args:
            state: Current state

        Returns:
            List of messages
        """
        return state.messages

    def _call_llm(
        self, prompt: str, state: AgentState, system_prompt: Optional[str] = None
    ) -> str:
        """Call the LLM with a prompt and chat history.

        Args:
            prompt: The prompt to send to the LLM
            state: Current state
            system_prompt: Optional system prompt override

        Returns:
            LLM response
        """
        messages = [
            {"role": "system", "content": system_prompt or self._get_system_prompt()}
        ]

        # Add chat history
        for msg in self._get_chat_history(state):
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            else:
                messages.append({"role": "assistant", "content": msg.content})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}", exc_info=True)
            raise

    def _update_state(self, state: AgentState, **kwargs) -> None:
        """Update the state with new values.

        Args:
            state: Current state
            **kwargs: Key-value pairs to update in state
        """
        state.update(**kwargs)
