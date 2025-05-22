import sys
import os
import logging

sys.dont_write_bytecode = True

from utils.format_validation import is_weekday, convert_to_date_obj, is_valid_symbol

logger = logging.getLogger(__name__)

STOCK_TEMPLATE = """
Collect daily stock information for {symbol} in {year}.
"""

STOCK_WITH_RANGE_TEMPLATE = """
Collect daily stock information for {symbol} between {start_date} and {end_date}.
"""

STOCK_WITH_DATE_TEMPLATE = """
Collect daily stock information for stocks {symbols} on {date}.
"""


def stock_collection_prompt(
    symbol: str | None = None,
    year: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    symbols: list[str] | None = None,
    date: str | None = None,
) -> str:
    if symbols:
        if not is_weekday(date):
            raise ValueError("Date must be a weekday (Monday-Friday)")
        else:
            date = convert_to_date_obj(date).strftime("%Y-%m-%d")
        is_valid_symbol(symbols)
        prompt = STOCK_WITH_DATE_TEMPLATE.format(symbols=symbols, date=date)
    elif start_date and end_date:
        if not is_weekday(start_date) or not is_weekday(end_date):
            raise ValueError("Start and end dates must be weekdays (Monday-Friday)")
        else:
            start_date = convert_to_date_obj(start_date).strftime("%Y-%m-%d")
            end_date = convert_to_date_obj(end_date).strftime("%Y-%m-%d")
        is_valid_symbol(symbol)
        prompt = STOCK_WITH_RANGE_TEMPLATE.format(
            symbol=symbol, start_date=start_date, end_date=end_date
        )
    else:
        is_valid_symbol(symbol)
        prompt = STOCK_TEMPLATE.format(symbol=symbol, year=year)
    return prompt
