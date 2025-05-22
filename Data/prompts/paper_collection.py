import sys
import os


sys.dont_write_bytecode = True

PAPER_TRACK_TEMPLATE = """
Collect a dataset that contains all accepted papers from {conference_name} {year} {track}.
"""

PAPER_TEMPLATE = """
Collect a dataset that contains all accepted papers from {conference_name} {year}.
"""

PAPER_YEAR_TEMPLATE = """
Collect a dataset that contains all accepted papers from {conference_name} in year range {start_year} to {end_year}.
"""


def paper_collection_from_conference_prompt(
    conference_name: str,
    year: int = None,
    track: str = None,
    start_year: int = None,
    end_year: int = None,
    func: str = None,
) -> str:
    if track:
        prompt = PAPER_TRACK_TEMPLATE.format(
            conference_name=conference_name, year=year, track=track
        )
    elif start_year and end_year:
        prompt = PAPER_YEAR_TEMPLATE.format(
            conference_name=conference_name, start_year=start_year, end_year=end_year
        )
    else:
        prompt = PAPER_TEMPLATE.format(conference_name=conference_name, year=year)
    return prompt
