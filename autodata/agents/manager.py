import sys
import logging
from typing import List, Callable, Optional
from easydict import EasyDict
from pydantic import BaseModel, Field

from autodata.agents.base import BaseAgent, BaseResponse
from autodata.agents.res import RESEARCH_AGENTS
from autodata.agents.dev import DEVELOPMENT_AGENTS
from autodata.core.types import AgentState
from autodata.prompts.prompt_loader import load_prompt

sys.dont_write_bytecode = True
logger = logging.getLogger(__name__)


class ManagerResponse(BaseResponse):
    message: str = Field(description="Hướng dẫn hoặc thông điệp cần gửi.")
    next: str = Field(description="Agent tiếp theo để thực hiện nhiệm vụ.")
    reasoning: str = Field(description="Lý do hoặc cơ sở để chuyển tiếp nhiệm vụ.")
    status: str = Field(default="running", description="Trạng thái hiện tại của workflow.")


class ManagerAgent(BaseAgent):
    """Agent điều phối toàn bộ pipeline crawl dữ liệu."""

    def __init__(
        self,
        agent_name: str = "ManagerAgent",
        description: str = "A manager agent to orchestrate multi-agent workflow.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: BaseModel = ManagerResponse,
        **kwargs,
    ):
        instruction = load_prompt(
            "manager",
            WORKER_NAMES=RESEARCH_AGENTS + DEVELOPMENT_AGENTS
        )

        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("✅ ManagerAgent initialized successfully")

    async def __call__(self, state: AgentState, model=None):
        """Điều phối workflow giữa các agent."""
        llm = model if model is not None else self._model
        assert llm, "ManagerAgent requires an LLM instance."

        try:
            chain = self._prompt | llm.with_structured_output(self._output_parser)
            response = chain.invoke(state)

            next_agent = response.next.strip().replace("\n", "")
            reasoning = response.reasoning.strip()
            next_agent = self.route_agent(next_agent)

            logger.info(f"📍 Manager decided to move to: {next_agent}")
            logger.debug(f"Reasoning: {reasoning}")

            # ✅ Cập nhật trực tiếp vào state
            state["messages"].append(response.message)
            state["next"] = next_agent

            return state

        except Exception as e:
            logger.error(f"❌ ManagerAgent error: {e}", exc_info=True)
            state["messages"].append(f"[Manager Error] {str(e)}")
            state["next"] = "[END]"
            return state

    def route_agent(self, next_agent: str) -> str:
        """Tự động định tuyến agent kế tiếp."""
        name = next_agent.lower()

        if "planner" in name:
            return "WebAgent"
        if "web" in name:
            return "ToolAgent"
        if "tool" in name:
            return "EngineerAgent"
        if "engineer" in name:
            return "TestAgent"
        if "test" in name:
            return "ValidationAgent"
        if "validation" in name or "done" in name or "finish" in name:
            return "[END]"
        return "ManagerAgent"
