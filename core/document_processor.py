
from core.operation_factory import OperationFactory


class DocumentProcessor:

    async def process(self, document_config, context):

        for operation in document_config["Operations"]:

            service = OperationFactory.get(operation)

            await service.execute(context)