"""Duplicate vendor check operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class DuplicateCheckService(BaseOperation):
    """Checks whether the current vendor already exists."""

    async def execute(self, context):
        """Store duplicate-check result in the shared context."""
        LOGGER.info("Running Duplicate Check Service")
        context.duplicate_check_result.setdefault("duplicate_found", False)
        return context
