"""Compatibility wrapper for logging helpers now located in core.logging."""

from core.logging import (  # noqa: F401
    activity_details_from_activity,
    activity_log_details,
    configure_logging,
    get_logger,
)
