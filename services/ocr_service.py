"""OCRService operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class OCRService(BaseOperation):
    """Execute the OCR workflow operation."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running OCRService")
        context.ocr_result[context.document_type or "current"] = {"status": "completed"}
        return context
