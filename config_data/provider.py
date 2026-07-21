"""Configuration provider abstraction for the current JSON-backed data source."""

from __future__ import annotations

from pathlib import Path

from config_data.country_config import ConfigService


class JsonConfigProvider(ConfigService):
    """JSON-backed provider; can be replaced by a DB-backed implementation later."""

    def __init__(self, config_path: str | Path = "config_data/countries.json") -> None:
        super().__init__(config_path)
