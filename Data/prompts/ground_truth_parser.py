import sys
import os
import os.path as osp
from easydict import EasyDict
from typing import Optional
import logging

sys.dont_write_bytecode = True

from utils.function import normalize
from utils.io import load_file
from utils.format_validation import is_weekday, convert_to_date_obj, is_valid_symbol

logger = logging.getLogger(__name__)

CONF_NAME_MAPPING = {
    "NeurIPS": "NeurIPS",
    "ICML": "ICML",
    "ICLR": "ICLR",
    "ACL": "ACL",
    "EMNLP": "EMNLP",
    "NAACL": "NAACL",
}
ATTRIBUTES = [
    "TITLE",
    "AUTHORS",
    "ABSTRACT",
    "CONFERENCE",
    "ABBR",
    "TRACK",
    "PAPER_LINK",
    "BIBTEX_LINK",
    "SUPP_LINK",
]
TRACKS = [
    "Main Conference Track",
    "Datasets and Benchmark Track",
    "Long Paper Track",
    "Short Paper Track",
    "Findings Track",
]


def parse_academic_paper(
    conference_name: str,
    year: Optional[int | str] = None,
    track: str = None,
    start_year: Optional[int | str] = None,
    end_year: Optional[int | str] = None,
    attributes: Optional[list[str]] = None,
    data_dir: str = None,
) -> EasyDict:

    if attributes is None:
        attributes = ATTRIBUTES
    elif isinstance(attributes, list):
        for attr in attributes:
            if attr not in ATTRIBUTES:
                raise ValueError(f"Invalid attribute: {attr}")
    if track is not None:
        if track not in TRACKS:
            raise ValueError(f"Invalid track: {track}")
        if not year:
            raise ValueError("Year must be provided when track is specified")

    conf_name = CONF_NAME_MAPPING.get(conference_name, None)
    res = {}
    if not conf_name:
        raise ValueError(
            f"Conference name {conference_name} is not supported. Please check the conference name."
        )
    work_dir = osp.join(data_dir, conf_name)
    if (start_year is not None and end_year is None) or (
        start_year is None and end_year is not None
    ):
        raise ValueError(
            "Both start_year and end_year must be provided together or both should be None"
        )

    if start_year and end_year:
        for y in range(int(start_year), int(end_year) + 1):

            data = load_file(
                osp.join(work_dir, y, f"paper_metadata_{conf_name}_{year}.json")
            )
            for index, paper in data.items():
                title = normalize(paper["TITLE"])
                identifier = f"{title}_{conf_name}_{year}"
                res[identifier] = {
                    key: (
                        paper[key]
                        if not key.endswith("_LINKS")
                        else paper["LINKS"][key.split("_")[0]]
                    )
                    for key in attributes
                }
    elif track:
        data = load_file(
            osp.join(work_dir, track, f"paper_metadata_{conf_name}_{year}.json")
        )
        for _, paper in data.items():
            if paper["TRACK"] == track:
                title = normalize(paper["TITLE"])
                identifier = f"{title}_{conf_name}_{year}"
                res[identifier] = {
                    key: (
                        paper[key]
                        if not key.endswith("_LINKS")
                        else paper["LINKS"][key.split("_")[0]]
                    )
                    for key in attributes
                }
    elif year:
        data = load_file(osp.join(work_dir, f"paper_metadata_{conf_name}_{year}.json"))
        for _, paper in data.items():
            title = normalize(paper["TITLE"])
            identifier = f"{title}_{conf_name}_{year}"
            res[identifier] = {
                key: (
                    paper[key]
                    if not key.endswith("_LINK")
                    else paper["LINKS"][key.split("_")[0]]
                )
                for key in attributes
            }
    else:
        raise ValueError("Either year or track must be provided")
    return res


def parse_stock_data(
    symbol: str,
    year: Optional[int | str | None] = None,
    start_date: Optional[str | None] = None,
    end_date: Optional[str | None] = None,
    symbols: Optional[list[str] | None] = None,
    date: Optional[str | None] = None,
    data_dir: str = None,
) -> EasyDict:
    res = {}
    if symbols:
        if not is_weekday(date):
            raise ValueError("Date must be a weekday (Monday-Friday)")
        else:
            date = convert_to_date_obj(date).strftime("%Y-%m-%d")
        for symbol in symbols:
            assert is_valid_symbol(symbol)
            res[symbol] = parse_stock_data(
                symbol=symbol,
                year=year,
                start_date=date,
                end_date=date,
                symbols=[],
                date=None,
                data_dir=data_dir,
            )
    elif start_date and end_date:
        if not is_weekday(start_date) or not is_weekday(end_date):
            raise ValueError("Start and end dates must be weekdays (Monday-Friday)")
        else:
            start_date = convert_to_date_obj(start_date).strftime("%Y-%m-%d")
            end_date = convert_to_date_obj(end_date).strftime("%Y-%m-%d")
        assert is_valid_symbol(symbol)
        data = load_file(
            osp.join(data_dir, f"{symbol}_2015-01-01_2024-12-31.csv"),
            output_type="original",
        )
        res = data[(data["date"] >= start_date) & (data["date"] <= end_date)]
        res = res.to_dict(orient="records")
        for idx, record in enumerate(res):
            format_record = {
                "Date": record["date"],
                "Open": record["open"],
                "High": record["high"],
                "Low": record["low"],
                "Close": record["close"],
                "Volume": record["volume"],
                "adjOpen": record["adjOpen"],
                "adjHigh": record["adjHigh"],
                "adjLow": record["adjLow"],
                "adjClose": record["adjClose"],
                "adjVolume": record["adjVolume"],
                "divCash": record["divCash"],
            }
            res[idx] = format_record
    elif year:
        assert is_valid_symbol(symbol)
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        res = parse_stock_data(
            symbol=symbol,
            year=year,
            start_date=start_date,
            end_date=end_date,
            symbols=[],
            date=None,
            data_dir=data_dir,
        )
    else:
        raise ValueError("Either symbols or date must be provided")
    return res


def parse_mlb_data(
    data_type: str,
    team: Optional[str | None] = None,
    start_year: Optional[str | None] = None,
    end_year: Optional[str | None] = None,
    teams: Optional[list[str] | None] = None,
    year: Optional[int | str | None] = None,
    data_dir: str = None,
) -> EasyDict:
    res = {}
    if teams:
        for team in teams:
            res[team] = parse_mlb_data(
                data_type=data_type,
                team=team,
                year=year,
                start_year=year,
                end_year=year,
                teams=[],
            )
    elif start_year and end_year:
        data = load_file(
            osp.join(data_dir, data_type.lower(), f"{team}.csv"), output_type="original"
        )
        for year in range(int(start_year), int(end_year) + 1):
            res[year] = data[data["YEAR"] == year]
    elif team:
        data = load_file(
            osp.join(data_dir, data_type.lower(), f"{team}.csv"), output_type="original"
        )
        res = data.to_dict(orient="records")
    else:
        raise ValueError("Either teams or year must be provided")
    return res
