"""State of a single user's onboarding journey."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from models.progress import ProgressState


class WorkflowPhase(str, Enum):
    """The stage of the conversation the user is currently in."""

    START = "start"
    COUNTRY_SELECTED = "country_selected"
    OPERATION_SELECTED = "operation_selected"
    AWAITING_DOCUMENT = "awaiting_document"
    PROCESSING = "processing"
    AWAITING_FORM = "awaiting_form"
    AWAITING_REVIEW = "awaiting_review"
    CREATING_VENDOR = "creating_vendor"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentStatus(str, Enum):
    """Lifecycle status for one configured document stage."""

    PENDING = "PENDING"
    WAITING_FOR_UPLOAD = "WAITING_FOR_UPLOAD"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WaitingFor(str, Enum):
    """External user input the workflow is currently paused for."""

    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    FORM = "FORM"
    REVIEW = "REVIEW"


@dataclass
class DocumentWorkflowState:
    """Runtime state for a single document workflow stage."""

    status: DocumentStatus = DocumentStatus.PENDING
    files: list[str] = field(default_factory=list)
    progress_activity_id: str | None = None
    current_step_index: int = 0
    steps: dict[str, str] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


@dataclass
class WorkflowState:
    """Mutable state for one user's onboarding session."""

    phase: WorkflowPhase = WorkflowPhase.START
    country: str | None = None
    operation: str | None = None
    current_document: str | None = None
    collected_documents: list[str] = field(default_factory=list)
    progress: ProgressState | None = None
    current_workflow_index: int = 0
    workflow_status: str = "STARTED"
    waiting_for: WaitingFor | None = None
    documents: dict[str, DocumentWorkflowState] = field(default_factory=dict)
    form_data: dict[str, str | None] = field(default_factory=dict)
    review_confirmed: bool = False
    vendor_created: bool = False
