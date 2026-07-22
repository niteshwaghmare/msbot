"""Owns all transitions of the live simulation progress state.

ProgressService is the single component permitted to mutate a
ProgressState. It builds the state from configured process steps and
advances it through the pending -> running -> completed lifecycle.
FakeProcessor drives it; ProgressCard reads the resulting snapshot.
"""

from __future__ import annotations

from models.country import ProcessStep
from models.progress import ProgressState, ProgressStep, StepStatus


class ProgressService:
    """Builds and advances the simulated process state.

    The service wraps a single ProgressState and exposes the minimal
    set of transitions needed to run the simulation. It performs no I/O
    and no waiting, keeping it deterministic and unit-testable.
    """

    def __init__(self, steps: list[ProcessStep]) -> None:
        """Initialise the service from configured process steps.

        Args:
            steps: The ordered process steps from configuration. Each is
                converted into a live ProgressStep in PENDING status.

        Raises:
            ValueError: If no steps are supplied.
        """
        if not steps:
            raise ValueError("ProgressService requires at least one step.")
        self._state = ProgressState(
            steps=[
                ProgressStep(id=step.id, title=step.title)
                for step in steps
            ],
            current_index=-1,
        )

    @property
    def state(self) -> ProgressState:
        """The current progress snapshot, for rendering."""
        return self._state

    def start(self) -> ProgressStep:
        """Begin the process by activating the first step.

        Returns:
            The first step, now in RUNNING status.
        """
        self._state.current_index = 0
        first = self._state.steps[0]
        first.status = StepStatus.RUNNING
        return first

    def complete_step(self) -> None:
        """Mark the currently running step as completed.

        Raises:
            RuntimeError: If there is no active step to complete.
        """
        current = self._current()
        current.status = StepStatus.COMPLETED

    def next_step(self) -> ProgressStep | None:
        """Advance to and activate the next pending step.

        Returns:
            The newly activated step in RUNNING status, or None if the
            final step has already been reached.

        Raises:
            RuntimeError: If called before the process has started.
        """
        if self._state.current_index < 0:
            raise RuntimeError("Cannot advance before start().")
        if self._state.current_index >= len(self._state.steps) - 1:
            return None
        self._state.current_index += 1
        nxt = self._state.steps[self._state.current_index]
        nxt.status = StepStatus.RUNNING
        return nxt

    def fail(self) -> None:
        """Mark the currently running step as failed.

        Raises:
            RuntimeError: If there is no active step to fail.
        """
        current = self._current()
        current.status = StepStatus.FAILED

    def complete(self) -> None:
        """Mark the process finished by clearing the active index.

        Completing the final step leaves every step COMPLETED; this
        resets current_index to the not-active sentinel so the card
        renders a finished, rather than in-progress, state.
        """
        self._state.current_index = -1

    def _current(self) -> ProgressStep:
        """Return the currently active step.

        Returns:
            The step at the active index.

        Raises:
            RuntimeError: If no step is currently active.
        """
        idx = self._state.current_index
        if idx < 0 or idx >= len(self._state.steps):
            raise RuntimeError("No active step.")
        return self._state.steps[idx]