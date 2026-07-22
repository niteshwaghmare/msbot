"""Logging helpers for the Vendor Onboarding bot.

The bot handles multiple Teams conversations at the same time, so every
turn log should include stable conversation and user identifiers.  This
module centralises that extraction so handlers, routers, and flows log the
same fields consistently.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from botbuilder.core import TurnContext
from botbuilder.schema import Activity

LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "conversation_id=%(conversation_id)s "
    "channel_id=%(channel_id)s "
    "user_id=%(user_id)s "
    "user_name=%(user_name)s "
    "activity_id=%(activity_id)s "
    "activity_type=%(activity_type)s "
    "%(message)s"
)

_DEFAULT_ACTIVITY_DETAILS: dict[str, str] = {
    "conversation_id": "-",
    "channel_id": "-",
    "user_id": "-",
    "user_name": "-",
    "activity_id": "-",
    "activity_type": "-",
}


class ActivityContextFilter(logging.Filter):
    """Ensure activity context fields always exist on log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in _DEFAULT_ACTIVITY_DETAILS.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


def configure_logging() -> None:
    """Configure application logging once.

    The log level can be adjusted with ``LOG_LEVEL`` (for example,
    ``DEBUG`` or ``WARNING``). Logs go to stderr by default, which keeps
    them compatible with local runs and container log collectors.
    """

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format=LOG_FORMAT)
    context_filter = ActivityContextFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(context_filter)
    for handler in root_logger.handlers:
        handler.addFilter(context_filter)


def get_logger(name: str) -> logging.Logger:
    """Return a logger that is safe to use with or without activity extras."""

    logger = logging.getLogger(name)
    logger.addFilter(ActivityContextFilter())
    return logger


def activity_log_details(turn_context: TurnContext) -> dict[str, str]:
    """Extract stable conversation and sender details for log records.

    Args:
        turn_context: The current Bot Framework turn context.

    Returns:
        A dictionary suitable for ``logger.info(..., extra=...)``.
    """

    return activity_details_from_activity(turn_context.activity)


def activity_details_from_activity(activity: Activity) -> dict[str, str]:
    """Extract stable conversation and sender details from an activity."""

    conversation = getattr(activity, "conversation", None)
    sender = getattr(activity, "from_property", None)

    return {
        "conversation_id": _string_or_dash(getattr(conversation, "id", None)),
        "channel_id": _string_or_dash(getattr(activity, "channel_id", None)),
        "user_id": _string_or_dash(getattr(sender, "id", None)),
        "user_name": _string_or_dash(getattr(sender, "name", None)),
        "activity_id": _string_or_dash(getattr(activity, "id", None)),
        "activity_type": _string_or_dash(getattr(activity, "type", None)),
    }


def _string_or_dash(value: Any) -> str:
    """Return a log-safe string for optional Bot Framework fields."""

    if value is None or value == "":
        return "-"
    return str(value).replace("\n", " ").replace("\r", " ")
