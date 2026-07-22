"""Routes Adaptive Card submit actions to controller methods.

The router is the single mapping from a card's submit `action` to the
WorkflowController method that handles it. It reads the structured
payload only; it never parses button titles or holds flow logic.
"""

from __future__ import annotations

from typing import Any

from botbuilder.core import TurnContext

from cards.country_select_card import ACTION_SELECT_COUNTRY
from cards.operation_card import ACTION_SELECT_OPERATION
from cards.document_upload_card import ACTION_SUBMIT_DOCUMENTS
from flows.vendor_create.create_flow import WorkflowController


class CardRouter:
    """Dispatches card submit payloads to the workflow controller."""

    def __init__(self, controller: WorkflowController) -> None:
        """Initialise the router.

        Args:
            controller: The workflow controller whose methods handle each
                routed action.
        """
        self._controller = controller

    async def route(
        self, turn_context: TurnContext, payload: dict[str, Any] | None
    ) -> None:
        """Dispatch a submit payload to the matching controller method.

        A missing or unrecognised payload restarts the flow at the
        country card, so stale cards or plain text always land somewhere
        sensible.

        Args:
            turn_context: The current turn context.
            payload: The card submit payload (activity.value), or None
                for a plain text message.
        """
        action = (payload or {}).get("action")

        if action == ACTION_SELECT_COUNTRY:
            await self._controller.handle_country(
                turn_context, payload["country"]
            )
        elif action == ACTION_SELECT_OPERATION:
            await self._controller.handle_operation(
                turn_context, payload["operation"]
            )
        elif action == ACTION_SUBMIT_DOCUMENTS or bool(turn_context.activity.attachments):
            await self._controller.handle_submit(turn_context, payload)
        else:
            # Unknown action, or plain text: (re)start the flow.
            await self._controller.show_countries(turn_context)