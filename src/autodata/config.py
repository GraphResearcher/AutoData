"""Configuration management for AutoData."""

import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Global settings for AutoData.
    
    This class manages all configuration settings for the package,
    with support for environment variables and .env files.
    """
    
    # LLM Configuration
    llm_api_key: str = Field(..., env="LLM_API_KEY")
    llm_model: str = Field("gpt-4", env="LLM_MODEL")
    llm_temperature: float = Field(0.7, env="LLM_TEMPERATURE")
    
    # Agent Configuration
    max_agents: int = Field(3, env="MAX_AGENTS")
    agent_timeout: int = Field(30, env="AGENT_TIMEOUT")
    
    # HTTP Configuration
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings() 