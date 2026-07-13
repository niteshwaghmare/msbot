"""Core activity handler for the Vendor Onboarding demo bot.

Thin Bot Framework adapter: it extracts the submit payload (or lack of
one) from each activity and delegates every decision to the card router.
It holds no flow logic itself.
"""

from __future__ import annotations

from typing import Any

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount

from bot.card_router import CardRouter


class DemoActivityHandler(ActivityHandler):
    """Handles incoming Teams activities by delegating to the router.

    The router (and through it the controller) owns all flow behaviour;
    this class only translates Bot Framework events into router calls.
    """

    def __init__(self, router: CardRouter) -> None:
        """Initialise the handler.

        Args:
            router: The card router that dispatches submit payloads.
        """
        super().__init__()
        self._router = router

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Route a message or card submit.

        Card submits arrive as message activities with no text but a
        populated `value`; plain text has no `value`. Both are handed to
        the router, which decides what happens.

        Args:
            turn_context: The current turn context.
        """
        payload: dict[str, Any] | None = turn_context.activity.value
        await self._router.route(turn_context, payload)

    async def on_members_added_activity(
        self,
        members_added: list[ChannelAccount],
        turn_context: TurnContext,
    ) -> None:
        """Show the country card to each newly added user.

        Args:
            members_added: Accounts that just joined the conversation.
            turn_context: The current turn context.
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # No payload: the router starts the flow at the country card.
                await self._router.route(turn_context, None)