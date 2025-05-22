PAPER_DATA_FORMAT_TEMPLATE = """
The dataset format should be a dictionary with the following keys:
- TITLE: the title of the paper
- AUTHORS: the authors of the paper
- ABSTRACT: the abstract of the paper
- CONFERENCE: the conference of the paper, i.e., "Proceedings of the 30th International Conference on Machine Learning".
- ABBR: the abbreviation of the conference, i.e., "ICML".
- TRACK: the track of the paper, i.e., "Main Conference Track".
- PAPER_LINK: the permanent link of the paper, i.e., "http://proceedings.mlr.press/v28/levine13.pdf".
- BIBTEX_LINK: the permanent link of the bibtex.
- SUPP_LINK: the link of the supplementary, i.e., "http://proceedings.mlr.press/v28/levine13-supp.pdf".
"""


STOCK_DATA_FORMAT_TEMPLATE = """
The dataset format should be a dictionary with the following keys: 
- Date: The date of the stock in format YYYY-MM-DD.
- Open: Open trading day price.
- High: Highest price within the trading day.
- Low: Lowest price within the trading day.
- Close: Close trading day price.
- Volume: Total number of shares traded within the trading day.
- adjOpen: Open trading day price, adjusted by coporate actions.
- adjHigh: Highest price within the trading day, adjusted by coporate actions.
- adjLow: Lowest price within the trading day, adjusted by coporate actions.
- adjClose: Close trading day price, adjusted by coporate actions.
- adjVolume: Total number of shares traded within the trading day, adjusted for stock splits.
- divCash: The cash dividend distrbuted per share.
"""


MLB_PITCHING_DATA_FORMAT_TEMPLATE = """
The dataset format should be a dictionary with the following keys:
- TEAM_NAME: The full name of the team.
- TEAM_ABBR: The abbreviation of the team.
- YEAR: The calendar year of the season.
- W: The number of wins.
- L: The number of losses.
- ERA: The earned run average (runs allowed per nine innings).
- GS: The number of games started.
- CG: The number of complete games pitched.
- SHO: The number of shutouts pitched.
- SV: The number of saves.
- IP: The number of innings pitched.
- H: The number of hits allowed.
- R: The number of runs allowed.
- ER: The number of earned runs allowed.
- HR: The number of home runs allowed.
- HB: The number of hit batters.
- BB: The number of walks allowed (bases on balls).
- SO: The number of strikeouts.
"""


MLB_HITTING_DATA_FORMAT_TEMPLATE = """
The dataset format should be a dictionary with the following keys:
- TEAM_NAME: The full name of the team.
- TEAM_ABBR: The abbreviation of the team.
- YEAR: The calendar year of the season.
- AB: The number of official at-bats.
- R: The number of runs scored.
- HR: The number of home runs.
- H: The number of hits reaching at least first base.
- 2B: The number of doubles (reaching second base).
- 3B: The number of triples (reaching third base).
- RBI: The number of runs batted in.
- BB: The number of walks (bases on balls).
- SO: The number of strikeouts.
- SB: The number of stolen bases.
- CS: The number of times caught stealing.
"""
