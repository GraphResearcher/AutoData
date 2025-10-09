import sys
import os
from typing import Callable, Optional, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import logging
from easydict import EasyDict
from autodata.tools.web import get_page_content


sys.dont_write_bytecode = True

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from autodata.core.types import AgentState
from autodata.agents.base import BaseAgent, BaseResponse
from autodata.prompts.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class BrowserAction(BaseResponse):
    action: str = Field(description="Type of browser action", pattern="^(search|open|extract|click|scroll)$")
    query: Optional[str] = Field(None, description="Search query if action==search")
    url: Optional[str] = Field(None, description="URL if action==open or extract")
    selector: Optional[str] = Field(None, description="CSS selector or XPath if action==extract or click")
    notes: Optional[str] = Field(None, description="Optional short note")

class Step(BaseResponse):
    name: str = Field(description="The name of the step.")
    description: str = Field(description="The description of the step.")
    output: str = Field(description="The expected output of the step.")


class PlannerResponse(BaseResponse):
    thought: str = Field(description="A thinking step to complete the given user task.")
    steps: List[Step] = Field(
        description="A list of detailed steps to complete the task."
    )

class PlannerAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "PlannerAgent",
        description: str = "A planner agent to plan the data collection process.",
        model: Callable = None,
        tools=None,
        **kwargs,
    ):
        parser = PydanticOutputParser(pydantic_object=PlannerResponse)

        # ép Gemini sinh JSON
        model = model.with_structured_output(PlannerResponse)
        instruction = (
                "You are a Planning Agent.\n"
                "Your ONLY output must be valid JSON conforming to the schema below.\n"
                "If you write anything else, the system will fail.\n\n"
                + load_prompt("planner")
                + "\n\nReturn ONLY the JSON object. Start with '{' and end with '}'."
        )

        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=None,  # bỏ parser, vì llm đã tự structured
        )

        logger.info("PlannerAgent initialized successfully")


class ToolAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "ToolAgent",
        description: str = "A tool agent to execute browser or data extraction actions.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("tool")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("ToolAgent initialized successfully")

    async def __call__(self, state: dict | AgentState, model=None):
        """Execute browser/data collection actions (from WebAgent)."""
        llm = model if model is not None else self._model
        assert llm is not None, "Please provide a valid LLM for ToolAgent."

        # Lấy thông tin từ state (LangGraph truyền vào)
        if isinstance(state, dict):
            messages = state.get("messages", [])
        else:
            messages = getattr(state, "messages", [])

        # Lấy message cuối cùng (WebAgent vừa gửi)
        if not messages:
            logger.warning("No messages received in ToolAgent.")
            return EasyDict({"messages": ["No input message found."], "next": "ManagerAgent"})

        last_msg = messages[-1]
        content = getattr(last_msg, "content", str(last_msg))

        import re
        import json

        # Làm sạch chuỗi JSON (loại bỏ ```json, ``` và escape)
        try:
            clean_json = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE)
            clean_json = clean_json.replace("\\n", "\n").replace("\\", "")
            action_data = json.loads(clean_json)
        except Exception as e:
            logger.warning(f"ToolAgent: Could not parse JSON from WebAgent output. Error: {e}")
            return EasyDict({
                "messages": [f"Invalid JSON input from WebAgent: {e}"],
                "agent_next": "ManagerAgent"
            })

        # Đọc action và URL
        action_type = action_data.get("action")
        url = action_data.get("url")

        # Thực thi hành động tương ứng
        if action_type in ["get_page_content", "open"] and url:
            try:
                html = get_page_content(url)
                if html:
                    logger.info(f"ToolAgent successfully fetched HTML from {url}")
                    return EasyDict({
                        "messages": [f"Successfully fetched HTML content from {url} ({len(html)} chars)."],
                        "html_content": html,
                        "next": "BlueprintAgent",  # đi thẳng tới BlueprintAgent, tránh vòng lặp
                    })
                else:
                    return EasyDict({
                        "messages": [f"Failed to fetch content from {url}."],
                        "next": "ManagerAgent",
                    })
            except Exception as e:
                logger.error(f"ToolAgent: error fetching content from {url}: {e}")
                return EasyDict({
                    "messages": [f"Error fetching page content: {e}"],
                    "next": "ManagerAgent",
                })

        # Không hỗ trợ hành động khác
        logger.warning(f"ToolAgent: Unsupported action '{action_type}'")
        return EasyDict({
            "messages": [f"No valid tool action executed for '{action_type}'."],
            "next": "ManagerAgent",
        })


class WebResponse(BaseResponse):
    pass


class BlueprintAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "BlueprintAgent",
        description: str = "A blueprint agent to create a development blueprint for the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("blueprint")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=None,
        )
        logger.info("BlueprintAgent initialized successfully")

class WebAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "WebAgent",
        description: str = "A web agent to search the web for the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        #output_parser: Optional[BaseModel] = None,  # bỏ parser JSON
        **kwargs,
    ):
        instruction = load_prompt("browser")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=BrowserAction,  # <-- thêm dòng này để không ép JSON
        )
        logger.info("WebAgent initialized successfully")

''''
class WebAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "WebAgent",
        description: str = "A web agent to search the web for the data collection process.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = None,
        **kwargs,
    ):
        instruction = load_prompt("browser")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,
        )
        logger.info("WebAgent initialized successfully")
'''
class BlueprintResponse(BaseResponse):
    logic: str = Field(description="The programming logic for data collection.")
    test_plan: str = Field(description="The test plan for debugging the program.")
    validation_plan: str = Field(description="The validation plan for verifying data accuracy.")

class BlueprintAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str = "BlueprintAgent",
        description: str = "A blueprint agent to create a structured development blueprint in JSON format.",
        model: Callable = None,
        tools: Optional[List[Callable]] = None,
        output_parser: Optional[BaseModel] = BlueprintResponse,
        **kwargs,
    ):
        instruction = load_prompt("blueprint")
        super().__init__(
            agent_name=agent_name,
            instruction=instruction,
            description=description,
            model=model,
            tools=tools,
            output_parser=output_parser,  # ép parse JSON theo schema
        )
        logger.info("BlueprintAgent initialized successfully")


RESEARCH_AGENTS = [
    PlannerAgent.__name__,
    WebAgent.__name__,
    BlueprintAgent.__name__,
]

