"""Live state for the simulated onboarding process.

Unlike the configuration models, these objects are mutable and change
as the simulation advances. ProgressService owns the transitions;
ProgressCard renders the current snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class StepStatus(str, Enum):
    """Lifecycle status of a single process step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressStep:
    """A process step paired with its current runtime status.

    Attributes:
        id: Matches the configured ProcessStep.id.
        title: Display label, copied from config for rendering.
        status: Current lifecycle status of this step.
    """

    id: str
    title: str
    status: StepStatus = StepStatus.PENDING


@dataclass
class ProgressState:
    """Snapshot of the whole simulated process.

    Attributes:
        steps: All steps in execution order, each with live status.
        current_index: Index of the active step, or -1 before start /
            after completion.
    """

    steps: list[ProgressStep] = field(default_factory=list)
    current_index: int = -1

    @property
    def is_complete(self) -> bool:
        """True when every step has completed successfully."""
        return bool(self.steps) and all(
            step.status is StepStatus.COMPLETED for step in self.steps
        )

    @property
    def has_failed(self) -> bool:
        """True when any step has failed."""
        return any(step.status is StepStatus.FAILED for step in self.steps)