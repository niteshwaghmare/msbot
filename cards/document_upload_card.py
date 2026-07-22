"""Builder for the document-upload Adaptive Card.

Prompts for one required document at a time. In local environments the
card asks for a file path; in deployed environments it tells the user to
attach a file. The submit action advances the workflow to the next
required document or to processing.
"""

from __future__ import annotations

from typing import Any

from botbuilder.schema import Attachment

from utils.adaptive_card_loader import build_card, to_attachment

# Action identifier carried in the submit button's payload.
ACTION_SUBMIT_DOCUMENTS: str = "submit_documents"


class UploadCard:
    """Builds the card listing required documents with a submit action."""

    @staticmethod
    def render(
        documents: list[str],
        country: str,
        current_document: str | None = None,
        is_local: bool = False,
        upload_config: dict[str, str] | None = None,
    ) -> Attachment:
        """Build the document-upload card.

        Args:
            documents: Required document types, from configuration.
            country: The selected country, shown for context.
            current_document: The document currently being requested.
            is_local: Whether to prompt for a local file path.

        Returns:
            A Bot Framework attachment carrying the upload card.

        Raises:
            ValueError: If no documents are supplied.
        """
        if not documents:
            raise ValueError("Cannot render upload card with no documents.")

        current_document = current_document or documents[0]

        upload_config = upload_config or {}
        body: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": upload_config.get("title", "Upload required documents"),
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
            {
                "type": "TextBlock",
                "text": upload_config.get("prompt", f"Please provide: {current_document}"),
                "wrap": True,
                "spacing": "Medium",
            },
        ]

        if is_local:
            body.append(
                {
                    "type": "Input.Text",
                    "id": "document_path",
                    "placeholder": "Enter the full file path",
                    "label": "File path",
                }
            )
        else:
            body.append(
                {
                    "type": "TextBlock",
                    "text": "Upload the file as an attachment for this document.",
                    "wrap": True,
                    "spacing": "Small",
                    "isSubtle": True,
                }
            )

        actions: list[dict[str, Any]] = [
            {
                "type": "Action.Submit",
                "title": "Continue",
                "data": {
                    "action": ACTION_SUBMIT_DOCUMENTS,
                    "document": current_document,
                },
            }
        ]

        return to_attachment(build_card(body, actions))