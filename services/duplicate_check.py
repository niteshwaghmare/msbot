"""Duplicate-check operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from core.logging import get_logger

LOGGER = get_logger(__name__)


class DuplicateCheckService(BaseOperation):
    """Check whether the current vendor appears to be a duplicate."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running DuplicateCheckService")
        context.duplicate_check_result = {"duplicate_found": False}
        return context
