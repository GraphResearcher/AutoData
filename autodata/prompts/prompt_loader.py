import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)

# Đường dẫn mặc định đến thư mục chứa prompts
PROMPT_DIR = Path(__file__).parent

# Bộ nhớ cache để tránh đọc file lặp lại
_PROMPT_CACHE: Dict[str, str] = {}

def load_prompt(name: str, **kwargs: Any) -> str:
    """
    Tải và render prompt từ file Markdown (hoặc .txt), có hỗ trợ Jinja2 template.

    Args:
        name (str): Tên prompt (ví dụ: "planner", "web", "tool")
        **kwargs: Các biến truyền vào Jinja2 (ví dụ TOOL_NAMES, WORKER_NAMES,...)

    Returns:
        str: Chuỗi prompt hoàn chỉnh đã được render
    """

    try:
        # Kiểm tra cache trước
        if name in _PROMPT_CACHE:
            prompt_template = _PROMPT_CACHE[name]
            if kwargs:
                return _render_template(prompt_template, **kwargs)
            return prompt_template

        # Xác định đường dẫn file prompt
        prompt_path_md = PROMPT_DIR / f"{name}.md"
        prompt_path_txt = PROMPT_DIR / f"{name}.txt"

        if prompt_path_md.exists():
            file_path = prompt_path_md
        elif prompt_path_txt.exists():
            file_path = prompt_path_txt
        else:
            raise FileNotFoundError(
                f"Không tìm thấy prompt '{name}'. Hãy kiểm tra tên file trong thư mục /prompts."
            )

        # Đọc nội dung file
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Lưu cache
        _PROMPT_CACHE[name] = prompt_template

        # Render nếu có biến Jinja
        rendered = _render_template(prompt_template, **kwargs) if kwargs else prompt_template

        logger.info(f"✅ Prompt '{name}' đã được tải thành công từ {file_path.name}")
        return rendered

    except Exception as e:
        logger.error(f"❌ Lỗi khi tải prompt '{name}': {e}")
        raise


def _render_template(template_str: str, **kwargs: Any) -> str:
    """
    Render template bằng Jinja2.
    """
    try:
        env = Environment(
            loader=FileSystemLoader(str(PROMPT_DIR)),
            autoescape=select_autoescape(["html", "xml"])
        )
        template = env.from_string(template_str)
        return template.render(**kwargs)
    except Exception as e:
        logger.error(f"❌ Lỗi khi render Jinja2 cho prompt: {e}")
        raise
