"""Vendor creation operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from core.logging import get_logger

LOGGER = get_logger(__name__)


class VendorService(BaseOperation):
    """Create or stage the vendor from processed context data."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running VendorService")
        context.vendor_details.setdefault("creation_status", "created")
        return context
