"""TINService operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class TINService(BaseOperation):
    """Execute the TIN workflow operation."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running TINService")
        context.tax_details[context.document_type or "current"] = {"status": "completed"}
        return context
