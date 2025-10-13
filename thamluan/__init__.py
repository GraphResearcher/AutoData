"""
AutoData - AI Agent Crawler System
Multi-agent system for crawling and analyzing Vietnamese law documents.
"""

__version__ = "1.0.0"
__author__ = "AutoData Team"

from core.config import config
from core.auto import run_workflow, run_workflow_async

__all__ = ["config", "run_workflow", "run_workflow_async"]