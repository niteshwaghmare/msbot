"""ValidationService operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from core.logging import get_logger

LOGGER = get_logger(__name__)


class ValidationService(BaseOperation):
    """Execute the Validation workflow operation."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running ValidationService")
        context.validation_result[context.document_type or "current"] = {"status": "completed"}
        return context
