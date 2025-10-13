"""
Prompt Loader - Load markdown prompts và replace variables.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Get prompts directory
PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Load prompt từ markdown file và replace variables.

    Args:
        filename: Tên file prompt (ví dụ: "manager_system.md")
        variables: Dictionary of variables để replace trong prompt

    Returns:
        Prompt string với variables replaced
    """
    filepath = PROMPTS_DIR / filename

    if not filepath.exists():
        # Return default prompt nếu file không tồn tại
        return f"You are a helpful AI agent for the AutoData system."

    with open(filepath, 'r', encoding='utf-8') as f:
        prompt = f.read()

    # Replace variables nếu có
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))

    return prompt


# Export for convenience
__all__ = ["load_prompt"]