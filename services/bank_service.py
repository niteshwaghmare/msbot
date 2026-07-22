"""Bank workflow operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class BankService(BaseOperation):
    """Executes the Bank processing step."""

    async def execute(self, context):
        """Update the shared context with Bank execution metadata."""
        LOGGER.info("Running Bank Service")
        data = getattr(context, "bank_details")
        data["bank_executed"] = True
        if context.document_type:
            data.setdefault("document_type", context.document_type)
        return context
