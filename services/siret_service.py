"""SIRET workflow operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class SIRETService(BaseOperation):
    """Executes the SIRET processing step."""

    async def execute(self, context):
        """Update the shared context with SIRET execution metadata."""
        LOGGER.info("Running SIRET Service")
        data = getattr(context, "tax_details")
        data["siret_executed"] = True
        if context.document_type:
            data.setdefault("document_type", context.document_type)
        return context
