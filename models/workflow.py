"""State of a single user's onboarding journey.

Tracks the user's selections and their current phase in the flow.
WorkflowService owns all transitions; controllers read this state to
decide how to route the next interaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from models.progress import ProgressState


class WorkflowPhase(str, Enum):
    """The stage of the conversation the user is currently in."""

    START = "start"
    COUNTRY_SELECTED = "country_selected"
    OPERATION_SELECTED = "operation_selected"
    AWAITING_DOCUMENT = "awaiting_document"
    PROCESSING = "processing"
    COMPLETED = "completed"


@dataclass
class WorkflowState:
    """Mutable state for one user's onboarding session.

    Attributes:
        phase: Current phase in the conversation flow.
        country: Selected country name, once chosen.
        operation: Selected operation label, once chosen.
        current_document: The document currently being collected.
        collected_documents: Paths or attachment references collected so far.
        progress: Live progress state, present during/after processing.
    """

    phase: WorkflowPhase = WorkflowPhase.START
    country: str | None = None
    operation: str | None = None
    current_document: str | None = None
    collected_documents: list[str] = field(default_factory=list)
    progress: ProgressState | None = None