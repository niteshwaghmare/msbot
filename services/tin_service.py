"""TIN workflow operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class TINService(BaseOperation):
    """Executes the TIN processing step."""

    async def execute(self, context):
        """Update the shared context with TIN execution metadata."""
        LOGGER.info("Running TIN Service")
        data = getattr(context, "tax_details")
        data["tin_executed"] = True
        if context.document_type:
            data.setdefault("document_type", context.document_type)
        return context
