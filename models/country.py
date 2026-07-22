"""Typed representations of the workflow configuration file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentConfig:
    """Document configuration for a country."""

    document_type: str
    display_name: str
    operations: list[str]
    min_files: int = 1
    allow_multiple: bool = False


@dataclass(frozen=True)
class WorkflowStep:
    """A single configured workflow stage."""

    id: str
    title: str
    type: str
    operation: str | None = None
    document: str | None = None
    card: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Country:
    """A country available for vendor onboarding."""

    name: str
    country_code: str
    currency: str
    documents: list[DocumentConfig]
    workflow: list[WorkflowStep]

    @property
    def document_types(self) -> list[str]:
        """Document type identifiers in configured order."""
        return [document.document_type for document in self.documents]


# Backward-compatible alias used by ProgressService.
ProcessStep = WorkflowStep


@dataclass(frozen=True)
class WorkflowConfig:
    """The fully parsed workflow configuration."""

    countries: dict[str, Country]
    operations: list[str]
    operation_registry: dict[str, str] = field(default_factory=dict)
    step_delay_seconds: float = 0.0

    def get_country(self, name: str) -> Country | None:
        """Return the country by display name, or None if absent."""
        return self.countries.get(name)
