"""Typed representations of the country-driven workflow configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentConfig:
    """Document requirements and operations from configuration."""

    document_type: str
    display_name: str
    operations: list[str]
    min_files: int = 1
    allow_multiple: bool = False


@dataclass(frozen=True)
class WorkflowStep:
    """A configured workflow step."""

    id: str
    title: str
    type: str
    document: str | None = None
    operation: str | None = None
    card: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Country:
    """A country available for vendor onboarding."""

    name: str
    country_code: str
    currency: str
    documents: list[DocumentConfig]
    workflow: list[WorkflowStep]


@dataclass(frozen=True)
class ProcessStep:
    """Progress-compatible view of a configured workflow step."""

    id: str
    title: str


@dataclass(frozen=True)
class WorkflowConfig:
    """The fully parsed workflow configuration."""

    countries: dict[str, Country]
    operations: list[str]
    operation_registry: dict[str, str]
    step_delay_seconds: float = 0.0

    def get_country(self, name: str) -> Country | None:
        """Return the country by display name, or None if absent."""
        return self.countries.get(name)
