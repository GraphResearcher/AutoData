import sys
import os
import logging

sys.dont_write_bytecode = True

from utils.format_validation import (
    is_weekday,
    convert_to_date_obj,
    is_valid_symbol,
    is_valid_year,
    is_valid_nba_team,
)

logger = logging.getLogger(__name__)

NBA_TEAM_ALL_TEMPLATE = """
Collect NBA {team} all regular season stats until 2024.
"""

NBA_TEAM_RANGE_TEMPLATE = """
Collect NBA {team} all regular season stats from {start_year} to {end_year}.
"""

NBA_TEAM_ALL_YEAR_TEMPLATE = """
Collect all NBA regular season stats in {year}.
"""

NBA_PLAYER_ALL_TEMPLATE = """
Collect NBA player {player} all regular season stats until 2024.
"""

NBA_PLAYER_RANGE_TEMPLATE = """
Collect NBA player {player} regular season stats from {start_year} to {end_year}.
"""

NBA_PLAYERS_ALL_YEAR_TEMPLATE = """
Collect NBA players {players} all regular season stats in {year}.
"""

MLB_PITCHING_TEAM_TEMPLATE = """
Collect MLB {team} all regular season pitching stats until 2024.
"""

MLB_PITCHING_TEAM_RANGE_TEMPLATE = """
Collect MLB {team} regular season pitching stats from {start_year} to {end_year}.
"""

MLB_PITCHING_TEAM_ALL_YEAR_TEMPLATE = """
Collect all MLB regular season pitching stats in {year}.
"""

MLB_HITTING_TEAM_TEMPLATE = """
Collect MLB {team} all regular season hitting stats until 2024.
"""

MLB_HITTING_TEAM_RANGE_TEMPLATE = """
Collect MLB {team} regular season hitting stats from {start_year} to {end_year}.
"""

MLB_HITTING_TEAM_ALL_YEAR_TEMPLATE = """
Collect all MLB regular season hitting stats in {year}.
"""


def nba_team_collection_prompt(
    team: str | None = None,
    start_year: str | None = None,
    end_year: str | None = None,
    year: str | None = None,
) -> str:
    if not team:
        assert is_valid_year(year), "Invalid year"
        prompt = NBA_TEAM_ALL_YEAR_TEMPLATE.format(year=year)
    elif is_valid_year(start_year) and is_valid_year(end_year):
        assert is_valid_nba_team(team), "Invalid team"
        prompt = NBA_TEAM_RANGE_TEMPLATE.format(
            team=team, start_year=start_year, end_year=end_year
        )
    elif is_valid_nba_team(team):
        prompt = NBA_TEAM_ALL_TEMPLATE.format(team=team)
    else:
        raise ValueError("Invalid input")

    return prompt


def nba_player_collection_prompt(
    player: str | None = None,
    start_year: str | None = None,
    end_year: str | None = None,
    year: str | None = None,
    players: list[str] | None = None,
) -> str:
    if players:
        prompt = NBA_PLAYERS_ALL_YEAR_TEMPLATE.format(year=year, players=players)
    elif start_year and end_year:
        prompt = NBA_PLAYER_RANGE_TEMPLATE.format(
            player=player, start_year=start_year, end_year=end_year
        )
    elif player:
        prompt = NBA_PLAYER_ALL_TEMPLATE.format(player=player)
    else:
        raise ValueError("Invalid input")
    return prompt


def mlb_collection_prompt(
    data_type: str,  # PITCHING or HITTING
    team: str | None = None,
    start_year: str | None = None,
    end_year: str | None = None,
    year: str | None = None,
) -> str:

    if year:
        prompt = eval(f"MLB_{data_type}_TEAM_ALL_YEAR_TEMPLATE").format(year=year)
    elif start_year and end_year:
        prompt = eval(f"MLB_{data_type}_TEAM_RANGE_TEMPLATE").format(
            team=team, start_year=start_year, end_year=end_year
        )
    elif team:
        prompt = eval(f"MLB_{data_type}_TEAM_TEMPLATE").format(team=team)
    else:
        raise ValueError("Invalid input")
    return prompt
