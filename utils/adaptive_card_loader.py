"""Helpers for assembling Adaptive Cards and Teams attachments.

Centralises the Adaptive Card envelope (schema, type, version) and the
conversion to a Bot Framework Attachment, so individual card builders
produce only their dynamic body and never repeat boilerplate JSON.
"""

from __future__ import annotations

from typing import Any

from botbuilder.core import CardFactory
from botbuilder.schema import Attachment

# Adaptive Card schema constants. Defined once for the whole app.
_ADAPTIVE_CARD_SCHEMA: str = "http://adaptivecards.io/schemas/adaptive-card.json"
_ADAPTIVE_CARD_TYPE: str = "AdaptiveCard"
_ADAPTIVE_CARD_VERSION: str = "1.4"


def build_card(
    body: list[dict[str, Any]],
    actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Wrap a card body and actions in the Adaptive Card envelope.

    Args:
        body: The card's body elements, built dynamically by a card
            builder.
        actions: Optional action elements (buttons). Omitted from the
            output when None or empty.

    Returns:
        A complete Adaptive Card as a dictionary.
    """
    card: dict[str, Any] = {
        "$schema": _ADAPTIVE_CARD_SCHEMA,
        "type": _ADAPTIVE_CARD_TYPE,
        "version": _ADAPTIVE_CARD_VERSION,
        "body": body,
    }
    if actions:
        card["actions"] = actions
    return card


def to_attachment(card: dict[str, Any]) -> Attachment:
    """Convert a card dictionary into a Bot Framework attachment.

    Args:
        card: A complete Adaptive Card dictionary.

    Returns:
        An Attachment ready to attach to an outgoing activity.
    """
    return CardFactory.adaptive_card(card)