"""Dynamic Adaptive Card builder for configured workflow forms."""

from __future__ import annotations

from typing import Any

from botbuilder.schema import Attachment

from utils.adaptive_card_loader import build_card, to_attachment

ACTION_SUBMIT_VENDOR_INFORMATION = "submit_vendor_information"


class DetailsFormCard:
    """Builds the configured vendor-information form card."""

    @staticmethod
    def render(step: dict[str, Any], existing_values: dict[str, str | None] | None = None, errors: list[str] | None = None) -> Attachment:
        """Render a form from configured fields and submit metadata."""
        existing_values = existing_values or {}
        body: list[dict[str, Any]] = [
            {"type": "TextBlock", "text": step.get("title", "Vendor Information"), "weight": "Bolder", "size": "Medium"},
            {"type": "TextBlock", "text": step.get("prompt", "Please provide the remaining vendor details."), "wrap": True},
        ]
        if errors:
            body.append({"type": "TextBlock", "text": "\n".join(errors), "wrap": True, "color": "Attention"})
        for field in step.get("fields", []):
            field_type = field.get("type", "text")
            input_type = "Input.Text"
            item: dict[str, Any] = {
                "type": input_type,
                "id": field["id"],
                "label": field.get("label", field["id"]),
                "placeholder": field.get("placeholder", ""),
                "isRequired": bool(field.get("required", False)),
                "errorMessage": f"{field.get('label', field['id'])} is required.",
            }
            if field_type == "email":
                item["style"] = "Email"
            elif field_type == "tel":
                item["style"] = "Tel"
            elif field_type == "number":
                item["type"] = "Input.Number"
            elif field_type == "date":
                item["type"] = "Input.Date"
            if existing_values.get(field["id"]):
                item["value"] = existing_values[field["id"]]
            body.append(item)
        submit = step.get("submit", {})
        actions = [{"type": "Action.Submit", "title": submit.get("title", "Continue"), "data": {"action": submit.get("action", ACTION_SUBMIT_VENDOR_INFORMATION), "workflowStepId": step.get("id")}}]
        return to_attachment(build_card(body, actions))
