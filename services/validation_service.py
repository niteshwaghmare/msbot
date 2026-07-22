"""Validation workflow operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class ValidationService(BaseOperation):
    """Executes the Validation processing step."""

    async def execute(self, context):
        """Update the shared context with Validation execution metadata."""
        LOGGER.info("Running Validation Service")
        data = getattr(context, "validation_result")
        data["validation_executed"] = True
        if context.document_type:
            data.setdefault("document_type", context.document_type)
        return context
