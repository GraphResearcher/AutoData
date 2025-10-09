"""
Configuration management for the AutoData package.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, List
import yaml
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


def load_environment_variables_from_file(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file.

    Args:
        env_path: Optional path to .env file. If None, looks for .env in default locations.
    """
    if env_path:
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"✅ Loaded environment variables from: {env_path}")
        else:
            logger.warning(f"⚠️ Environment file not found: {env_path}")
    else:
        # Try to load from default locations
        default_env_paths = [
            Path.cwd() / ".env",
            Path.cwd() / ".env.local",
            Path.home() / ".autodata" / ".env",
        ]

        loaded = False
        for default_path in default_env_paths:
            if default_path.exists():
                load_dotenv(default_path)
                logger.info(f"✅ Loaded environment variables from: {default_path}")
                loaded = True
                break

        if not loaded:
            logger.info(
                "ℹ️ No .env file found in default locations. Using system environment variables."
            )

    # Verify essential environment variables are present
    verify_environment_variables()


def verify_environment_variables() -> None:
    """Verify that essential environment variables are present."""
    required_vars = []
    optional_vars = {
        "ANTHROPIC_API_KEY": "Anthropic Claude API access",
        "GOOGLE_API_KEY": "Google AI API access",
        "LANGSMITH_API_KEY": "LangSmith tracing and monitoring",
        "TAVILY_API_KEY": "Tavily search API access",
    }

    missing_vars = []
    available_vars = []

    for var, description in optional_vars.items():
        if os.getenv(var):
            available_vars.append(f"  ✅ {var}: {description}")
        else:
            missing_vars.append(f"  ❌ {var}: {description}")

    if available_vars:
        logger.info("🔑 Available API keys:")
        for var in available_vars:
            logger.info(var)

    if missing_vars:
        logger.warning("⚠️ Missing optional API keys (functionality may be limited):")
        for var in missing_vars:
            logger.warning(var)
        logger.warning(
            "💡 Add these to your .env file or set as environment variables for full functionality."
        )


class LLMConfig(BaseModel):
    """Configuration for LLM models."""

    ModelClass: str = Field(default="GoogleGenerativeAI")
    model: str = Field(default="gemini-2.5-flash")
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=593840)
    api_key: Optional[str] = Field(default=None)

    def get_additional_kwargs(self):
        """Trả về các tham số cần thiết."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key": self.api_key,  # Nếu có
        }
    def _get_additional_kwargs(self):
        """Alias để tương thích với các module khác (auto.py)"""
        return self.get_additional_kwargs()


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
    LLM_Config: LLMConfig = Field(default_factory=LLMConfig)
    Web_Config: WebConfig = Field(default_factory=WebConfig)
    Tool_Config: ToolConfig = Field(default_factory=ToolConfig)

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

    def initialize_llm(self) -> GoogleGenerativeAI:
        """Khởi tạo đối tượng GoogleGenerativeAI từ cấu hình LLMConfig."""
        # Đảm bảo rằng model và các tham số khác được truyền đúng
        return GoogleGenerativeAI(
            model=self.LLM_Config.model,  # Truyền model từ LLMConfig
            temperature=self.LLM_Config.temperature,
            max_tokens=self.LLM_Config.max_tokens,
            api_key=self.LLM_Config.api_key,  # Nếu có
        )


    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # LLM settings
        if os.getenv("GOOGLE_API_KEY"):
            self.llm.api_key = os.getenv("GOOGLE_API_KEY")

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
