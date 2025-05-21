"""Base agent implementation for AutoData."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from loguru import logger


class BaseAgent(ABC):
    """Base class for all AutoData agents.
    
    This abstract base class defines the interface that all agents must implement.
    Agents are responsible for specific tasks in the data collection pipeline.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the agent.
        
        Args:
            name: Unique identifier for the agent
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        logger.info(f"Initialized {self.__class__.__name__} agent: {name}")

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the agent's main task.
        
        This method must be implemented by all concrete agent classes.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            The result of the agent's execution
        """
        pass

    async def cleanup(self) -> None:
        """Clean up resources used by the agent.
        
        This method can be overridden by subclasses to implement custom cleanup logic.
        """
        logger.debug(f"Cleaning up {self.__class__.__name__} agent: {self.name}") 