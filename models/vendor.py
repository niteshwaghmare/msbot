"""Vendor domain models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VendorDetails:
    email: str | None = None
    phone: str | None = None


@dataclass
class Vendor:
    country: str | None = None
    operation: str | None = None
    details: VendorDetails = field(default_factory=VendorDetails)
    documents: list[str] = field(default_factory=list)
