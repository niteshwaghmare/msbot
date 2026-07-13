"""Simulated background processor standing in for a real task queue.

FakeProcessor advances a ProgressService through its steps with an
asyncio delay between each, invoking an async callback after every state
change so the caller can update the progress card in place. It contains
no Teams or Adaptive Card knowledge, so a Celery-backed driver can
replace it in Phase 2 without changing the UI layer.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from models.progress import ProgressState
from services.progress_service import ProgressService

# Async callback invoked after each state change. Receives the current
# ProgressState snapshot; the caller renders and sends/updates the card.
UpdateCallback = Callable[[ProgressState], Awaitable[None]]


class FakeProcessor:
    """Drives a ProgressService through its steps on a timed loop.

    The processor owns the *sequence and timing* of the simulation. It
    delegates state transitions to ProgressService and rendering to an
    injected callback, keeping it free of any UI dependency.
    """

    def __init__(
        self,
        progress: ProgressService,
        on_update: UpdateCallback,
        step_delay_seconds: float = 2.0,
    ) -> None:
        """Initialise the processor.

        Args:
            progress: The progress service whose state is advanced.
            on_update: Async callback invoked after every state change,
                given the current ProgressState to render.
            step_delay_seconds: Seconds to wait while each step is
                "running" before completing it.
        """
        self._progress = progress
        self._on_update = on_update
        self._delay = step_delay_seconds

    async def run(self) -> None:
        """Execute the full simulated process.

        Starts the first step, then for each step: renders the running
        state, waits, marks it completed, and advances. A final render
        reflects the completed state. Each render is delivered through
        the injected callback.
        """
        # Activate and render the first step as running.
        self._progress.start()
        await self._emit()

        # Complete the current step, then advance and render each next
        # step as running, until no steps remain.
        while True:
            await self._work()
            self._progress.complete_step()
            await self._emit()

            nxt = self._progress.next_step()
            if nxt is None:
                break
            await self._emit()

        # Clear the active index so the state reads as fully complete.
        self._progress.complete()
        await self._emit()

    async def _work(self) -> None:
        """Simulate the time a single step takes to run."""
        await asyncio.sleep(self._delay)

    async def _emit(self) -> None:
        """Deliver the current state snapshot to the update callback."""
        await self._on_update(self._progress.state)