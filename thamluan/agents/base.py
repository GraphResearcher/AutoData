"""
Base Agent - Lớp cơ sở cho tất cả agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from core.config import config
from core.types import AgentState, AgentRole, Task, TaskStatus, AgentMessage

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class cho tất cả agents"""

    def __init__(self, role: AgentRole, name: str, description: str):
        self.role = role
        self.name = name
        self.description = description

        # Initialize LLM
        self.llm = ChatOllama(
            model=config.LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            num_predict=config.LLM_MAX_TOKENS
        )

        logger.info(f"Initialized {self.name} ({self.role.value})")

    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute agent task.
        Mỗi agent phải implement method này.

        Args:
            state: Current AgentState

        Returns:
            Updated AgentState
        """
        pass

    def create_task(
        self,
        task_type: str,
        input_data: Dict[str, Any]
    ) -> Task:
        """
        Tạo task mới.

        Args:
            task_type: Loại task
            input_data: Input data cho task

        Returns:
            Task object
        """
        from core.types import TaskType

        task = Task(
            task_id=f"{self.role.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_type=TaskType(task_type),
            assigned_to=self.role,
            input_data=input_data
        )

        logger.info(f"Created task: {task.task_id} ({task.task_type.value})")
        return task

    def complete_task(
        self,
        task: Task,
        output_data: Dict[str, Any],
        error: Optional[str] = None
    ) -> Task:
        """
        Đánh dấu task hoàn thành.

        Args:
            task: Task cần complete
            output_data: Output data
            error: Error message nếu có

        Returns:
            Updated task
        """
        if error:
            task.status = TaskStatus.FAILED
            task.error_message = error
            logger.error(f"Task failed: {task.task_id} - {error}")
        else:
            task.status = TaskStatus.COMPLETED
            task.output_data = output_data
            logger.info(f"Task completed: {task.task_id}")

        task.completed_at = datetime.now()
        return task

    def update_state(
        self,
        state: AgentState,
        updates: Dict[str, Any]
    ) -> AgentState:
        """
        Update state với new data.

        Args:
            state: Current state
            updates: Dictionary of updates

        Returns:
            Updated state
        """
        state.update(updates)
        state['last_updated'] = datetime.now()
        state['current_agent'] = self.role

        return state

    def log_error(
        self,
        state: AgentState,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Log error vào state.

        Args:
            state: Current state
            error_message: Error message
            details: Additional details

        Returns:
            Updated state
        """
        error_entry = {
            'agent': self.role.value,
            'message': error_message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }

        state['errors'].append(error_entry)
        logger.error(f"{self.name} error: {error_message}")

        return state

    def log_warning(
        self,
        state: AgentState,
        warning_message: str
    ) -> AgentState:
        """
        Log warning vào state.

        Args:
            state: Current state
            warning_message: Warning message

        Returns:
            Updated state
        """
        state['warnings'].append(f"[{self.role.value}] {warning_message}")
        logger.warning(f"{self.name} warning: {warning_message}")

        return state

    async def call_llm(
        self,
        system_prompt: str,
        user_message: str
    ) -> str:
        """
        Call LLM với prompt.

        Args:
            system_prompt: System prompt
            user_message: User message

        Returns:
            LLM response
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]

            response = await self.llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    def should_continue(self, state: AgentState) -> bool:
        """
        Check xem workflow có nên tiếp tục không.

        Args:
            state: Current state

        Returns:
            True nếu nên tiếp tục
        """
        # Stop nếu có quá nhiều errors
        if len(state.get('errors', [])) > 5:
            logger.warning("Too many errors, stopping workflow")
            return False

        return True

    def get_task_history(self, state: AgentState) -> list:
        """
        Lấy task history của agent này.

        Args:
            state: Current state

        Returns:
            List of tasks
        """
        return [
            task for task in state.get('task_history', [])
            if task.assigned_to == self.role
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role={self.role.value}, name={self.name})"