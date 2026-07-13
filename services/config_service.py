"""Loads and exposes the workflow configuration.

ConfigService is the single component that reads config/workflow.json.
It parses the file into typed models once at construction and serves
the rest of the application through typed accessor methods, so no other
component ever handles the raw JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from models.config_models import Country, ProcessStep, WorkflowConfig


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


class ConfigService:
    """Loads workflow configuration and serves it as typed models.

    The configuration is read and validated once at construction. All
    accessors operate on the in-memory WorkflowConfig, so callers pay
    the file-read cost only at startup.
    """

    def __init__(self, config_path: str | Path) -> None:
        """Load and parse the configuration file.

        Args:
            config_path: Path to the workflow JSON configuration file.

        Raises:
            ConfigError: If the file is missing, is not valid JSON, or
                does not match the expected structure.
        """
        self._path = Path(config_path)
        self._config: WorkflowConfig = self._load()

    def _load(self) -> WorkflowConfig:
        """Read the file and build a validated WorkflowConfig.

        Returns:
            The parsed configuration.

        Raises:
            ConfigError: On any read, parse, or structural error.
        """
        raw = self._read_file()
        return self._parse(raw)

    def _read_file(self) -> dict:
        """Read and JSON-decode the configuration file.

        Returns:
            The raw configuration as a dictionary.

        Raises:
            ConfigError: If the file is missing or not valid JSON.
        """
        if not self._path.is_file():
            raise ConfigError(f"Config file not found: {self._path}")
        try:
            with self._path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as error:
            raise ConfigError(f"Invalid JSON in {self._path}: {error}") from error

    def _parse(self, raw: dict) -> WorkflowConfig:
        """Convert a raw config dict into a typed WorkflowConfig.

        Args:
            raw: The decoded JSON dictionary.

        Returns:
            The typed, validated configuration.

        Raises:
            ConfigError: If required keys are missing or malformed.
        """
        try:
            countries = {
                name: Country(name=name, documents=list(body["documents"]))
                for name, body in raw["countries"].items()
            }
            operations = list(raw["operations"])
            process = [
                ProcessStep(id=step["id"], title=step["title"])
                for step in raw["process"]
            ]
        except (KeyError, TypeError) as error:
            raise ConfigError(f"Malformed configuration: {error}") from error

        if not countries:
            raise ConfigError("Configuration defines no countries.")
        if not operations:
            raise ConfigError("Configuration defines no operations.")
        if not process:
            raise ConfigError("Configuration defines no process steps.")

        delay = raw.get("simulation", {}).get("step_delay_seconds", 2.0)
        return WorkflowConfig(
            countries=countries,
            operations=operations,
            process=process,
            step_delay_seconds=float(delay),
        )

    def get_countries(self) -> list[str]:
        """Return all country display names, in configured order.

        Returns:
            The list of country names.
        """
        return list(self._config.countries.keys())

    def get_country(self, name: str) -> Country | None:
        """Return a single country by display name.

        Args:
            name: The country display name.

        Returns:
            The matching Country, or None if not found.
        """
        return self._config.get_country(name)

    def get_documents(self, name: str) -> list[str]:
        """Return the required documents for a country.

        Args:
            name: The country display name.

        Returns:
            The document types for that country.

        Raises:
            ConfigError: If the country is not configured.
        """
        country = self._config.get_country(name)
        if country is None:
            raise ConfigError(f"Unknown country: {name}")
        return list(country.documents)

    def get_operations(self) -> list[str]:
        """Return all operation labels, in configured order.

        Returns:
            The list of operation labels.
        """
        return list(self._config.operations)

    def get_process(self) -> list[ProcessStep]:
        """Return the ordered process steps.

        Returns:
            The list of process steps driving the simulation.
        """
        return list(self._config.process)

    @property
    def step_delay_seconds(self) -> float:
        """The configured delay between simulated process steps."""
        return self._config.step_delay_seconds