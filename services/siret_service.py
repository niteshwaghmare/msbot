from core.base_operations import BaseOperation


class SIRETService(BaseOperation):

    async def execute(self, context):
        print("Running SIRET Service")
