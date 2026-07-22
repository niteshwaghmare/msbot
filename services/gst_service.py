"""GST workflow operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class GSTService(BaseOperation):
    """Executes the GST processing step."""

    async def execute(self, context):
        """Update the shared context with GST execution metadata."""
        LOGGER.info("Running GST Service")
        data = getattr(context, "tax_details")
        data["gst_executed"] = True
        if context.document_type:
            data.setdefault("document_type", context.document_type)
        return context
