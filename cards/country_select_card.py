"""Builder for the country-selection Adaptive Card.

Renders the configured countries as a dropdown input. Country names are
supplied by the caller from configuration; nothing is hardcoded here.
"""

from __future__ import annotations

from typing import Any

from botbuilder.schema import Attachment

from utils.adaptive_card_loader import build_card, to_attachment

# Action identifier carried in each button's submit payload. The card
# router matches on this to know a country was chosen.
ACTION_SELECT_COUNTRY: str = "select_country"


class CountryCard:
    """Builds the card that prompts the user to choose a country."""

    @staticmethod
    def render(countries: list[str]) -> Attachment:
        """Build the country-selection card for the given countries.

        Args:
            countries: Country display names, from configuration, in the
                order they should appear.

        Returns:
            A Bot Framework attachment carrying the country card.

        Raises:
            ValueError: If no countries are supplied.
        """
        if not countries:
            raise ValueError("Cannot render country card with no countries.")

        body: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": "Vendor Onboarding",
                "weight": "Bolder",
                "size": "Large",
            },
            {
                "type": "TextBlock",
                "text": "Select a country to begin.",
                "wrap": True,
                "spacing": "None",
                "isSubtle": True,
            },
            {
                "type": "Input.ChoiceSet",
                "id": "country",
                "style": "compact",
                "isMultiSelect": False,
                "choices": [
                    {"title": country, "value": country} for country in countries
                ],
                "placeholder": "Choose a country",
            },
        ]

        actions: list[dict[str, Any]] = [
            {
                "type": "Action.Submit",
                "title": "Continue",
                "data": {"action": ACTION_SELECT_COUNTRY},
            }
        ]

        return to_attachment(build_card(body, actions))