import sys
import os
import logging
from typing import Callable, Optional, List
from pydantic import BaseModel, Field

from autodata.agents.base import BaseAgent, BaseResponse
from autodata.prompts.prompt_loader import load_prompt

sys.dont_write_bytecode = True
logger = logging.getLogger(__name__)


# =========================================================
# 🧠 EngineerAgent – Viết code crawler, xử lý dữ liệu
# =========================================================
class EngineerResponse(BaseResponse):
    thought: str = Field(..., description="Reasoning or assumptions about the implementation.")
    dependencies: List[str] = Field(default_factory=list, description="List of required Python packages.")
    code: str = Field(..., description="Complete Python source code for the crawling or processing task.")
    explanation: str = Field(..., description="Explanation of how the code works and how to run it.")


class EngineerAgent(BaseAgent):
    """
    EngineerAgent dùng để sinh code thực thi (ví dụ crawler code) dựa trên keywords hoặc nhiệm vụ do ToolAgent cung cấp.
    """

    def __init__(
        self,
        agent_name: str = "EngineerAgent",
        description: str = "A code-generation agent that writes functional Python scripts.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = EngineerResponse,
        **kwargs,
    ):
        instruction = load_prompt("engineer")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("✅ EngineerAgent initialized successfully")


# =========================================================
# 🧪 TestAgent – Test code sinh ra
# =========================================================
class TestResponse(BaseResponse):
    test_summary: str = Field(description="Summary of test results.")
    success_rate: float = Field(default=0.0, description="Ratio of passed tests to total.")
    issues: List[str] = Field(default_factory=list, description="List of test failures or warnings, if any.")


class TestAgent(BaseAgent):
    """
    TestAgent dùng để kiểm thử code được sinh ra bởi EngineerAgent.
    """

    def __init__(
        self,
        agent_name: str = "TestAgent",
        description: str = "A test agent that validates generated code for correctness.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = TestResponse,
        **kwargs,
    ):
        instruction = load_prompt("test")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("✅ TestAgent initialized successfully")


# =========================================================
# ✅ ValidationAgent – Xác nhận chất lượng kết quả
# =========================================================
class ValidationResponse(BaseResponse):
    status: str = Field(description="Validation status: success or failed.")
    summary: str = Field(description="Summary of validation results.")
    issues: List[dict] = Field(default_factory=list, description="List of validation issues, if any.")


class ValidationAgent(BaseAgent):
    """
    ValidationAgent đánh giá kết quả cuối cùng — code có chạy đúng mục tiêu, dữ liệu có hợp lệ không.
    """

    def __init__(
        self,
        agent_name: str = "ValidationAgent",
        description: str = "A validation agent that ensures quality and compliance of results.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = ValidationResponse,
        **kwargs,
    ):
        instruction = load_prompt("valid")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("✅ ValidationAgent initialized successfully")


# =========================================================
# 📋 Danh sách Development Agents
# =========================================================
DEVELOPMENT_AGENTS = [
    EngineerAgent.__name__,
    TestAgent.__name__,
    ValidationAgent.__name__,
]
