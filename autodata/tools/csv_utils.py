"""
autodata.tools.csv_utils
Utilities to save list-of-dicts to CSV using pandas.
"""
import logging
import os
from typing import List, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def save_results_csv(records: List[Dict], out_path: str) -> str:
    """Save list of dict records into CSV; return path."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        df = pd.DataFrame(records)
        df.to_csv(out_path, index=False)
        logger.info("save_results_csv: saved %d rows -> %s", len(records), out_path)
        return out_path
    except Exception as e:
        logger.error("save_results_csv: failed to write %s: %s", out_path, e)
        raise
