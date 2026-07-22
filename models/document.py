"""Document domain models."""

from __future__ import annotations

from dataclasses import dataclass

DocumentType = str


@dataclass(frozen=True)
class DocumentSpec:
    type: DocumentType
    required: bool = True


@dataclass
class UploadedDoc:
    type: DocumentType
    value: str
