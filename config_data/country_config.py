"""Loads and exposes the country-driven workflow configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.country import (
    Country,
    DocumentConfig,
    ProcessStep,
    WorkflowConfig,
    WorkflowStep,
)


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


class ConfigService:
    """Loads workflow configuration and serves typed accessor methods."""

    def __init__(self, config_path: str | Path) -> None:
        self._path = Path(config_path)
        self._config: WorkflowConfig = self._load()

    def _load(self) -> WorkflowConfig:
        return self._parse(self._read_file())

    def _read_file(self) -> dict[str, Any]:
        if not self._path.is_file():
            raise ConfigError(f"Config file not found: {self._path}")
        try:
            with self._path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as error:
            raise ConfigError(f"Invalid JSON in {self._path}: {error}") from error

    def _parse(self, raw: dict[str, Any]) -> WorkflowConfig:
        try:
            countries = {
                name: self._parse_country(name, body)
                for name, body in raw["countries"].items()
            }
            registry = dict(raw.get("operationRegistry", {}))
        except (KeyError, TypeError) as error:
            raise ConfigError(f"Malformed configuration: {error}") from error

        if not countries:
            raise ConfigError("Configuration defines no countries.")
        return WorkflowConfig(
            countries=countries,
            operations=list(raw.get("operations", ["Create"])),
            operation_registry=registry,
            step_delay_seconds=float(
                raw.get("simulation", {}).get("step_delay_seconds", 0.0)
            ),
        )

    def _parse_country(self, name: str, body: dict[str, Any]) -> Country:
        documents = [
            DocumentConfig(
                document_type=item["documentType"],
                display_name=item.get("displayName", item["documentType"]),
                operations=list(item.get("operations", [])),
                min_files=int(item.get("minFiles", 1)),
                allow_multiple=bool(item.get("allowMultiple", False)),
            )
            for item in body.get("documents", [])
        ]
        workflow = [
            WorkflowStep(
                id=step["id"],
                title=step["title"],
                type=step["type"],
                document=step.get("document"),
                operation=step.get("operation"),
                card=step.get("card"),
                options={
                    k: v
                    for k, v in step.items()
                    if k
                    not in {"id", "title", "type", "document", "operation", "card"}
                },
            )
            for step in body.get("workflow", [])
        ]
        if not workflow:
            raise ConfigError(f"Country has no workflow: {name}")
        return Country(
            name=name,
            country_code=body.get("countryCode", ""),
            currency=body.get("currency", ""),
            documents=documents,
            workflow=workflow,
        )

    def get_countries(self) -> list[str]:
        return list(self._config.countries.keys())

    def get_country(self, name: str) -> Country | None:
        return self._config.get_country(name)

    def get_documents(self, name: str) -> list[str]:
        country = self._require_country(name)
        return [document.document_type for document in country.documents]

    def get_operations(self) -> list[str]:
        return list(self._config.operations)

    def get_workflow(self, name: str) -> list[WorkflowStep]:
        return list(self._require_country(name).workflow)

    def get_process(self, name: str | None = None) -> list[ProcessStep]:
        if name is None:
            first_country = next(iter(self._config.countries))
            name = first_country
        return [
            ProcessStep(id=step.id, title=step.title)
            for step in self.get_workflow(name)
        ]

    def _require_country(self, name: str) -> Country:
        country = self._config.get_country(name)
        if country is None:
            raise ConfigError(f"Unknown country: {name}")
        return country

    @property
    def step_delay_seconds(self) -> float:
        return self._config.step_delay_seconds
