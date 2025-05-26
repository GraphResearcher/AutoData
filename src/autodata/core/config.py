"""
Configuration management for the AutoData package.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for LLM models."""

    model_name: str = Field(default="gpt-4-turbo-preview")
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=2000)
    api_key: Optional[str] = Field(default=None)


class WebConfig(BaseModel):
    """Configuration for web browsing."""

    headless: bool = Field(default=True)
    timeout: int = Field(default=30)
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )


class ToolConfig(BaseModel):
    """Configuration for external tools."""

    google_api_key: Optional[str] = Field(default=None)
    google_cse_id: Optional[str] = Field(default=None)
    serper_api_key: Optional[str] = Field(default=None)


class AutoDataConfig(BaseModel):
    """Main configuration class for AutoData."""

    # Core settings
    log_level: str = Field(default="INFO")
    cache_dir: Path = Field(default=Path("cache"))
    output_dir: Path = Field(default=Path("output"))

    # Component configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    tools: ToolConfig = Field(default_factory=ToolConfig)

    @classmethod
    def from_file(cls, config_path: Optional[Path] = None) -> "AutoDataConfig":
        """Load configuration from a file.

        Args:
            config_path: Path to configuration file (YAML or JSON)

        Returns:
            AutoDataConfig instance
        """
        if config_path is None:
            return cls()

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        import yaml

        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    def to_file(self, config_path: Path) -> None:
        """Save configuration to a file.

        Args:
            config_path: Path to save configuration file
        """
        import yaml

        with open(config_path, "w") as f:
            yaml.dump(self.model_dump(), f)

    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # LLM settings
        if os.getenv("OPENAI_API_KEY"):
            self.llm.api_key = os.getenv("OPENAI_API_KEY")

        # Tool settings
        if os.getenv("GOOGLE_API_KEY"):
            self.tools.google_api_key = os.getenv("GOOGLE_API_KEY")
        if os.getenv("GOOGLE_CSE_ID"):
            self.tools.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if os.getenv("SERPER_API_KEY"):
            self.tools.serper_api_key = os.getenv("SERPER_API_KEY")

        # Core settings
        if os.getenv("AUTODATA_LOG_LEVEL"):
            self.log_level = os.getenv("AUTODATA_LOG_LEVEL")
        if os.getenv("AUTODATA_CACHE_DIR"):
            self.cache_dir = Path(os.getenv("AUTODATA_CACHE_DIR"))
        if os.getenv("AUTODATA_OUTPUT_DIR"):
            self.output_dir = Path(os.getenv("AUTODATA_OUTPUT_DIR"))
