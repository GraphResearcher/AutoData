import sys
import os


from easydict import EasyDict

sys.dont_write_bytecode = True

from utils.io import save_file
from .paper_collection import paper_collection_from_conference_prompt
from .stock_collection import stock_collection_prompt
from .sport_collection import (
    mlb_collection_prompt,
    nba_team_collection_prompt,
    nba_player_collection_prompt,
)
from .data_format import *


def random_prompt(config: dict | EasyDict) -> str:
    if isinstance(config, dict):
        config = EasyDict(config)

    instruct_config = config.get("instruct")
    data_format_config = config.get("data_format")


def build_prompt(config: dict | EasyDict) -> str:
    if isinstance(config, dict):
        config = EasyDict(config)

    instruct_config = config.get("instruct")
    data_format = config.get("data_format")
    if not isinstance(instruct_config, dict):
        raise ValueError("instruct must be a dictionary")
    instruct_func = globals()[instruct_config.get("func")]
    instruct_args = instruct_config.get("args")
    instruct_prompt = instruct_func(**instruct_args)
    data_format_prompt = globals()[data_format]

    task_instruction = "\n\n".join([instruct_prompt, data_format_prompt])

    return task_instruction
