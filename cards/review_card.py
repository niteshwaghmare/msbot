"""Adaptive Card builder for vendor review and confirmation."""

from __future__ import annotations

from typing import Any

from botbuilder.schema import Attachment

from models.workflow import WorkflowState
from utils.adaptive_card_loader import build_card, to_attachment

ACTION_CONFIRM_VENDOR = "confirm_vendor"
ACTION_EDIT_VENDOR_INFORMATION = "edit_vendor_information"


class ReviewCard:
    """Builds the review card from workflow state and configured actions."""

    @staticmethod
    def render(step: dict[str, Any], state: WorkflowState) -> Attachment:
        """Render country, document statuses, operation results, and form data."""
        body: list[dict[str, Any]] = [
            {"type": "TextBlock", "text": step.get("title", "Review & Confirm"), "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": f"Country\n{state.country}", "wrap": True},
            {"type": "TextBlock", "text": "Documents", "weight": "Bolder"},
        ]
        for doc_type, doc_state in state.documents.items():
            body.append({"type": "TextBlock", "text": f"{doc_type}: {doc_state.status.value}", "wrap": True, "spacing": "Small"})
        body.append({"type": "TextBlock", "text": "User-Provided Information", "weight": "Bolder"})
        labels = {"vatNumber": "VAT Number", "email": "Email", "phone": "Phone"}
        for key, value in state.form_data.items():
            body.append({"type": "TextBlock", "text": f"{labels.get(key, key)}: {value or ''}", "wrap": True, "spacing": "Small"})
        actions = [{"type": "Action.Submit", "title": action.get("title", action.get("id", "Continue")), "data": {"action": action.get("action"), "workflowStepId": step.get("id")}} for action in step.get("actions", [])]
        return to_attachment(build_card(body, actions))
