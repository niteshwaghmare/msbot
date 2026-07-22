"""Vendor creation operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class VendorService(BaseOperation):
    """Creates the vendor from the accumulated processing context."""

    async def execute(self, context):
        """Mark vendor creation as completed in the shared context."""
        LOGGER.info("Running Vendor Service")
        context.vendor_details.setdefault("created", True)
        return context
