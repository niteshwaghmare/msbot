"""Web scraping operation implementation."""

from __future__ import annotations

from core.base_operations import BaseOperation
from core.logging import get_logger

LOGGER = get_logger(__name__)


class WebScrapingService(BaseOperation):
    """Execute the web scraping workflow operation."""

    async def execute(self, context):
        """Update and return the shared processing context."""
        LOGGER.info("Running WebScrapingService")
        context.workflow_data["web_scraping"] = {"status": "completed"}
        return context
