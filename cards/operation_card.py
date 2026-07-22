"""Builder for the operation-selection Adaptive Card.

Renders the configured operations as submit buttons. Operation labels
are supplied by the caller from configuration; nothing is hardcoded.
"""

from __future__ import annotations

from typing import Any

from botbuilder.schema import Attachment

from utils.adaptive_card_loader import build_card, to_attachment

# Action identifier carried in each button's submit payload.
ACTION_SELECT_OPERATION: str = "select_operation"


class OperationCard:
    """Builds the card that prompts the user to choose an operation."""

    @staticmethod
    def render(operations: list[str], country: str) -> Attachment:
        """Build the operation-selection card.

        Args:
            operations: Operation labels, from configuration, in order.
            country: The already-selected country, shown for context.

        Returns:
            A Bot Framework attachment carrying the operation card.

        Raises:
            ValueError: If no operations are supplied.
        """
        if not operations:
            raise ValueError("Cannot render operation card with no operations.")

        body: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": "Choose an operation",
                "weight": "Bolder",
                "size": "Large",
            },
            {
                "type": "TextBlock",
                "text": f"Country: {country}",
                "wrap": True,
                "spacing": "None",
                "isSubtle": True,
            },
        ]

        actions: list[dict[str, Any]] = [
            {
                "type": "Action.Submit",
                "title": operation,
                "data": {
                    "msteams": {
                        "type": "messageBack",
                        "displayText": operation,
                        "text": operation,
                    },
                    "action": ACTION_SELECT_OPERATION,
                    "operation": operation,
                },
            }
            for operation in operations
        ]

        return to_attachment(build_card(body, actions))