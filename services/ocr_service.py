from core.base_operations import BaseOperation


class OCRService(BaseOperation):

    async def execute(self, context):
        print("Running OCR Service")