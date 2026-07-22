"""Typed representations of the workflow configuration file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentConfig:
    """Document metadata and upload validation configuration."""

    document_type: str
    display_name: str
    operations: list[str] = field(default_factory=list)
    required: bool = True
    min_files: int = 1
    max_files: int = 1
    allow_multiple: bool = False
    allowed_extensions: list[str] = field(default_factory=list)


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

    def get_document(self, document_type: str) -> DocumentConfig | None:
        """Return metadata for one configured document type."""
        return next((doc for doc in self.documents if doc.document_type == document_type), None)


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
