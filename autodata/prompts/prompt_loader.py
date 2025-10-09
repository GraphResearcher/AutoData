"""Utility to load markdown prompts and replace variables using Jinja2."""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Template


def load_prompt(agent_name: str, **variables: Any) -> str:
    """Load a markdown prompt for an agent and replace variables using Jinja2.
    
    Args:
        agent_name: Name of the agent (e.g., 'manager').
        **variables: Variables to replace in the prompt (e.g., agents=['agent1', 'agent2']).
    
    Returns:
        The prompt with variables replaced.
    
    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    prompt_path = Path(__file__).parent / f"{agent_name}.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = Template(f.read())
    return template.render(**variables)