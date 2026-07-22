from core.base_operations import BaseOperation


class WebScrapingService(BaseOperation):

    async def execute(self, context):
        print("Running Web Scraping Service")
