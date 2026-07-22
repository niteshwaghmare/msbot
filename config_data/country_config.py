"""Loads and exposes the workflow configuration.

ConfigService is the single component that reads config_data/countries.json.
It parses the file into typed models once at construction and serves
the rest of the application through typed accessor methods, so no other
component ever handles the raw JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from models.country import Country, DocumentConfig, WorkflowConfig, WorkflowStep


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
        """Convert a raw config dict into a typed WorkflowConfig."""
        try:
            countries = {}
            for name, body in raw["countries"].items():
                documents = [
                    DocumentConfig(
                        document_type=document["documentType"],
                        display_name=document.get("displayName", document["documentType"]),
                        operations=list(document.get("operations", [])),
                        required=bool(document.get("required", True)),
                        min_files=int(document.get("minFiles", 1)),
                        max_files=int(document.get("maxFiles", document.get("minFiles", 1))),
                        allow_multiple=bool(document.get("allowMultiple", False)),
                        allowed_extensions=list(document.get("allowedExtensions", [])),
                    )
                    for document in body.get("documents", [])
                ]
                workflow = [
                    WorkflowStep(
                        id=step["id"],
                        title=step["title"],
                        type=step["type"],
                        operation=step.get("operation"),
                        document=step.get("document"),
                        card=step.get("card"),
                        raw=dict(step),
                    )
                    for step in body.get("workflow", [])
                ]
                countries[name] = Country(
                    name=name,
                    country_code=body.get("countryCode", ""),
                    currency=body.get("currency", ""),
                    documents=documents,
                    workflow=workflow,
                )
            operations = list(raw["operations"])
            operation_registry = dict(raw.get("operationRegistry", {}))
        except (KeyError, TypeError, ValueError) as error:
            raise ConfigError(f"Malformed configuration: {error}") from error

        if not countries:
            raise ConfigError("Configuration defines no countries.")
        if not operations:
            raise ConfigError("Configuration defines no operations.")
        for country in countries.values():
            if not country.workflow:
                raise ConfigError(f"Country {country.name} defines no workflow.")
            self._validate_country(country)

        delay = raw.get("simulation", {}).get("step_delay_seconds", 0.0)
        return WorkflowConfig(
            countries=countries,
            operations=operations,
            operation_registry=operation_registry,
            step_delay_seconds=float(delay),
        )


    def _validate_country(self, country: Country) -> None:
        """Validate workflow references and document upload constraints."""
        document_types = set(country.document_types)
        seen_workflow_ids: set[str] = set()
        for document in country.documents:
            if document.min_files < 0 or document.max_files < document.min_files:
                raise ConfigError(f"Invalid minFiles/maxFiles for {country.name}.{document.document_type}.")
            if not document.allow_multiple and document.max_files > 1:
                raise ConfigError(f"allowMultiple false cannot have maxFiles > 1 for {country.name}.{document.document_type}.")

        for step in country.workflow:
            if step.id in seen_workflow_ids:
                raise ConfigError(f"Duplicate workflow id {step.id} in {country.name}.")
            seen_workflow_ids.add(step.id)
            if not step.type:
                raise ConfigError(f"Workflow step {step.id} missing type.")
            if step.type == "document":
                if not step.document:
                    raise ConfigError(f"Document workflow step {step.id} missing document reference.")
                if step.document not in document_types:
                    raise ConfigError(f"Workflow document {step.document} not present in documents for {country.name}.")
                nested_steps = step.raw.get("steps", [])
                if not nested_steps:
                    raise ConfigError(f"Document workflow step {step.id} has empty steps.")
                nested_ids: set[str] = set()
                for nested in nested_steps:
                    nested_id = nested.get("id")
                    if nested_id in nested_ids:
                        raise ConfigError(f"Duplicate nested workflow id {nested_id} in {step.id}.")
                    nested_ids.add(nested_id)
                    nested_type = nested.get("type")
                    if nested_type in {"operation", "decision"} and not nested.get("operation"):
                        raise ConfigError(f"Nested step {nested_id} missing operation name.")
                    if nested_type == "decision" and ("onSuccess" not in nested or "onDuplicate" not in nested):
                        raise ConfigError(f"Decision step {nested_id} missing decision outcomes.")
            elif step.type in {"operation", "decision"}:
                if not step.operation:
                    raise ConfigError(f"Workflow step {step.id} missing operation name.")
            elif step.type == "form":
                self._validate_form_step(country.name, step)
            elif step.type in {"review", "upload"}:
                if step.type == "upload" and step.document not in document_types:
                    raise ConfigError(f"Upload step {step.id} references unknown document {step.document}.")
            else:
                raise ConfigError(f"Unsupported workflow step type {step.type} in {country.name}.")

    def _validate_form_step(self, country_name: str, step: WorkflowStep) -> None:
        """Validate dynamic form field configuration."""
        allowed_types = {"text", "email", "tel", "number", "date", "choice"}
        fields = step.raw.get("fields", [])
        seen_fields: set[str] = set()
        for field in fields:
            field_id = field.get("id")
            if not field_id or field_id in seen_fields:
                raise ConfigError(f"Duplicate or missing form field id in {country_name}.{step.id}.")
            seen_fields.add(field_id)
            if field.get("type") not in allowed_types:
                raise ConfigError(f"Unknown form field type {field.get('type')} in {country_name}.{step.id}.")
        submit = step.raw.get("submit", {})
        if fields and not submit.get("action"):
            raise ConfigError(f"Form step {step.id} missing submit action.")

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
        return country.document_types


    def get_workflow(self, name: str) -> list[WorkflowStep]:
        """Return the configured workflow for a country.

        Args:
            name: The country display name.

        Returns:
            The workflow steps for that country.

        Raises:
            ConfigError: If the country is not configured.
        """
        country = self._config.get_country(name)
        if country is None:
            raise ConfigError(f"Unknown country: {name}")
        return list(country.workflow)

    def get_operations(self) -> list[str]:
        """Return all operation labels, in configured order.

        Returns:
            The list of operation labels.
        """
        return list(self._config.operations)

    def get_process(self) -> list[WorkflowStep]:
        """Return the ordered process steps.

        Returns:
            The list of process steps driving the simulation.
        """
        if not self._config.countries:
            return []
        first_country = next(iter(self._config.countries.values()))
        return list(first_country.workflow)

    @property
    def step_delay_seconds(self) -> float:
        """The configured delay between simulated process steps."""
        return self._config.step_delay_seconds