"""Shared runtime context for configuration-driven workflow execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessingContext:
    """Mutable state shared by every workflow operation.

    Operations receive this single object and enrich it as the onboarding
    workflow progresses. It deliberately uses dictionaries for extracted
    business data so new country-specific fields can be introduced in
    configuration without changing Python method signatures.
    """

    selected_country: str
    uploaded_files: dict[str, str] = field(default_factory=dict)
    document_type: str | None = None
    uploaded_file: str | None = None
    ocr_result: dict[str, Any] = field(default_factory=dict)
    extracted_fields: dict[str, Any] = field(default_factory=dict)
    validation_result: dict[str, Any] = field(default_factory=dict)
    bank_details: dict[str, Any] = field(default_factory=dict)
    tax_details: dict[str, Any] = field(default_factory=dict)
    vendor_details: dict[str, Any] = field(default_factory=dict)
    duplicate_check_result: dict[str, Any] = field(default_factory=dict)
    form_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    review_confirmed: bool = False
    workflow_terminated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
