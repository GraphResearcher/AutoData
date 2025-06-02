"""
AutoData Agents Package

This package contains all agent implementations for the AutoData multi-agent system.
"""

from .manager import ManagerAgent, ManagerResponse
from .base import BaseAgent, BaseResponse

# Research Group Agents
# from .planner import PlannerAgent, PlannerResponse
# from .web import WebAgent, WebResponse
# from .tool import ToolAgent, ToolResponse
# from .blueprint import BlueprintAgent, BlueprintResponse

# Development Group Agents
# from .engineer import EngineerAgent, EngineerResponse
# from .test import TestAgent, TestResponse
# from .validation import ValidationAgent, ValidationResponse

__all__ = [
    # Base classes
    "BaseAgent",
    "BaseResponse",
    # Manager Agent
    "ManagerAgent",
    "ManagerResponse",
    # Research Group Agents (commented out until implemented)
    # "PlannerAgent",
    # "PlannerResponse",
    # "WebAgent",
    # "WebResponse",
    # "ToolAgent",
    # "ToolResponse",
    # "BlueprintAgent",
    # "BlueprintResponse",
    # Development Group Agents (commented out until implemented)
    # "EngineerAgent",
    # "EngineerResponse",
    # "TestAgent",
    # "TestResponse",
    # "ValidationAgent",
    # "ValidationResponse",
]
