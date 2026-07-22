from core.base_operations import BaseOperation


class BankService(BaseOperation):

    async def execute(self, context):
        print("Running Bank Service")
