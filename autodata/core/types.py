"""
Types for the AutoData package.
"""

import sys
import os

from typing import TypedDict, Dict, List, Annotated, Union
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages


sys.dont_write_bytecode = True


class AgentState(TypedDict):
    """
    Represents the state of an agent in the system.

    Attributes:
        sender (str): The identifier of the agent sending messages
        next (str): The next agent to handle the state
        messages (list[BaseMessage]): A list of messages exchanged by the agent, annotated with the add_message function for message handling.
            Uses BaseMessage type from langchain for standardized message format.
    """

    sender: str
    next: str
    messages: Annotated[List[Union[HumanMessage, AIMessage]], add_messages]
