import os
import json
import logging
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """Configuration for the Ollama model."""
    model: str = Field(default="llama3.1:8b", description="Model name in Ollama")
    temperature: float = Field(default=0.3, description="Sampling temperature for generation")
    num_ctx: int = Field(default=4096, description="Context window size")
    base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")

class AutoDataConfig(BaseModel):
    """Main configuration class for AutoData framework."""
    LLM_Config: LLMConfig = Field(default_factory=LLMConfig)
    output_dir: Optional[str] = Field(default="./outputs", description="Directory for saving results")

    @classmethod
    def from_file(cls, file_path: Optional[Path] = None) -> "AutoDataConfig":
        """Load configuration from a JSON file if provided."""
        if not file_path:
            logger.warning("No config file path provided, using default settings.")
            return cls()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded configuration from {file_path}")
            return cls(**data)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse configuration file: {e}")
            raise

def load_environment_variables_from_file(env_path: Optional[Path] = None):
    """Load environment variables from a .env file if exists."""
    if not env_path:
        return
    if not os.path.exists(env_path):
        logger.warning(f".env file not found at {env_path}")
        return

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        logger.info(f"Environment variables loaded from {env_path}")
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        raise

# Optional helper if you ever need to manually init the model (for debugging)
def create_ollama_llm(model_name: str = "llama3.1:8b", temperature: float = 0.3) -> ChatOllama:
    """Standalone initializer for the Ollama LLM."""
    try:
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            num_ctx=4096,
            base_url="http://localhost:11434",
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChatOllama: {e}")
        raise
