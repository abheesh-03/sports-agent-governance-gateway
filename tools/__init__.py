"""Simulated business-system tools backed by fake JSON data."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# All fake data lives in the repository's top-level ``data`` directory.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=None)
def load_data(filename: str) -> Any:
    """Load and cache a JSON data file from the data directory."""
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)
