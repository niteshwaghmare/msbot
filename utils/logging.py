"""Logging helpers for the Vendor Onboarding bot.

The bot handles multiple Teams conversations at the same time, so every
turn log should include stable conversation and user identifiers.  This
module centralises that extraction so handlers, routers, and flows log the
same fields consistently.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

try:
    from botbuilder.core import TurnContext
    from botbuilder.schema import Activity
except ImportError:  # pragma: no cover - exercised in minimal environments
    TurnContext = Any
    Activity = Any

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
    ``DEBUG`` or ``WARNING``). Logs go to stderr by default, and can also
    be written to a file via ``LOG_FILE`` for container and local runs.
    """

    level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    third_party_loggers = [
        "msrest.universal_http",
        "msrest.universal_http.requests",
        "urllib3.connectionpool",
        "aiohttp.access",
    ]
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(LOG_FORMAT)
    context_filter = ActivityContextFilter()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)
    root_logger.addHandler(stream_handler)

    log_file = os.getenv("LOG_FILE")
    if not log_file:
        log_file = str(Path(__file__).resolve().parents[1] / "logs" / "app.log")

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)

    root_logger.addFilter(context_filter)


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
