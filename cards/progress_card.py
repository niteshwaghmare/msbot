"""Builder for the processing-progress Adaptive Card.

Renders the live ProgressState as a status list, one row per step with
an icon reflecting its status. This card carries no actions; it is
updated in place as the simulation advances.
"""

from __future__ import annotations

from typing import Any

from botbuilder.schema import Attachment

from models.progress import ProgressState, StepStatus
from utils.adaptive_card_loader import build_card, to_attachment

# Status icon shown at the start of each step row.
_STATUS_ICONS: dict[StepStatus, str] = {
    StepStatus.PENDING: "◻",
    StepStatus.RUNNING: "⏳",
    StepStatus.COMPLETED: "✅",
    StepStatus.FAILED: "❌",
}


class ProgressCard:
    """Builds the in-place-updated processing status card."""

    @staticmethod
    def render(state: ProgressState, title: str | None = None) -> Attachment:
        """Build the progress card for the current state.

        Args:
            state: The live progress snapshot to render.

        Returns:
            A Bot Framework attachment carrying the progress card.

        Raises:
            ValueError: If the state contains no steps.
        """
        if not state.steps:
            raise ValueError("Cannot render progress card with no steps.")

        heading = title or (
            "Vendor Created Successfully"
            if state.is_complete
            else "Processing…"
        )
        if title and state.is_complete:
            heading = f"{title} Completed"
        body: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": heading,
                "weight": "Bolder",
                "size": "Large",
            }
        ]

        for step in state.steps:
            icon = _STATUS_ICONS.get(step.status, "◻")
            body.append(
                {
                    "type": "TextBlock",
                    "text": f"{icon} {step.title}",
                    "wrap": True,
                    "spacing": "Small",
                }
            )

        # Deliberately no actions: this card is display-only and updated
        # in place after every stage.
        return to_attachment(build_card(body))