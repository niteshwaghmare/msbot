"""OCR workflow operation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from utils.logging import get_logger

LOGGER = get_logger(__name__)


class OCRService(BaseOperation):
    """Executes the OCR processing step."""

    async def execute(self, context):
        """Update the shared context with OCR execution metadata."""
        LOGGER.info("Running OCR Service")
        data = getattr(context, "ocr_result")
        data["ocr_executed"] = True
        if context.document_type:
            data.setdefault("document_type", context.document_type)
        return context
