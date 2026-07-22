from core.base_operations import BaseOperation


class TINService(BaseOperation):

    async def execute(self, context):
        print("Running TIN Service")
