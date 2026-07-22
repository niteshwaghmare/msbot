from core.base_operations import BaseOperation


class GSTService(BaseOperation):

    async def execute(self, context):
        print("Running GST Service")
