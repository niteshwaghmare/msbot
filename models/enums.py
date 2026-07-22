"""Shared enum aliases for vendor operations and statuses."""

from __future__ import annotations

from enum import Enum

from models.progress import StepStatus as DocStatus
from models.workflow import WorkflowPhase as VendorStatus


class Operation(str, Enum):
    """Supported vendor operations."""

    CREATE = "Create"
    REQUEST_CHECK = "Request Check"
    EXISTENCE_CHECK = "Existence Check"
