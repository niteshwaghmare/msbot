"""BankService operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class BankService(BaseOperation):
    """Execute the Bank workflow operation."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running BankService")
        context.bank_details[context.document_type or "current"] = {"status": "completed"}
        return context
