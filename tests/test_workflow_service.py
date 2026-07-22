import unittest

from flows.vendor_create.document_collector import WorkflowService, WorkflowError
from config_data.country_config import ConfigService
from models.workflow import WorkflowPhase


class WorkflowServiceDocumentFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ConfigService("config_data/countries.json")
        self.service = WorkflowService(self.config)

    def test_create_operation_collects_documents_one_by_one(self) -> None:
        self.service.start_workflow()
        self.service.select_country("France")
        self.service.select_operation("Create")

        self.service.begin_document_collection()
        state = self.service.get_state()

        self.assertEqual(state.phase, WorkflowPhase.AWAITING_DOCUMENT)
        self.assertEqual(self.service.get_current_document(), "AVIS")

        self.service.submit_document("/tmp/avis.pdf")
        state = self.service.get_state()
        self.assertEqual(state.phase, WorkflowPhase.AWAITING_DOCUMENT)
        self.assertEqual(self.service.get_current_document(), "RIB")

        self.service.submit_document("/tmp/rib.pdf")
        state = self.service.get_state()
        self.assertEqual(state.phase, WorkflowPhase.PROCESSING)
        self.assertEqual(state.collected_documents, ["/tmp/avis.pdf", "/tmp/rib.pdf"])

    def test_submit_document_requires_active_document_step(self) -> None:
        self.service.start_workflow()
        self.service.select_country("France")
        self.service.select_operation("Create")

        with self.assertRaises(WorkflowError):
            self.service.submit_document("/tmp/avis.pdf")

    def test_select_operation_accepts_messageback_text_variants(self) -> None:
        self.service.start_workflow()
        self.service.select_country("France")

        state = self.service.select_operation(" request check ")

        self.assertEqual(state.operation, "Request Check")
        self.assertEqual(state.phase, WorkflowPhase.OPERATION_SELECTED)


class CardRouterTests(unittest.IsolatedAsyncioTestCase):
    async def test_operation_route_falls_back_to_messageback_text(self) -> None:
        from types import SimpleNamespace

        from cards.operation_card import ACTION_SELECT_OPERATION
        from flows.router import CardRouter

        class ControllerStub:
            def __init__(self) -> None:
                self.operation: str | None = None

            async def handle_operation(self, turn_context, operation: str) -> None:
                self.operation = operation

        controller = ControllerStub()
        turn_context = SimpleNamespace(
            activity=SimpleNamespace(text="Request Check", attachments=[])
        )

        await CardRouter(controller).route(
            turn_context, {"action": ACTION_SELECT_OPERATION}
        )

        self.assertEqual(controller.operation, "Request Check")


class DocumentProcessorTests(unittest.IsolatedAsyncioTestCase):
    async def test_processor_executes_country_workflow_in_config_order(self) -> None:
        from core.document_processor import DocumentProcessor

        states = []

        async def on_update(state):
            states.append([step.status.value for step in state.steps])

        processor = DocumentProcessor(ConfigService("config_data/countries.json"))
        context = await processor.process(
            "France",
            {"AVIS": "/tmp/avis.pdf", "RIB": "/tmp/rib.pdf"},
            on_update,
        )

        self.assertEqual(context.selected_country, "France")
        self.assertTrue(context.ocr_result["ocr_executed"])
        self.assertTrue(context.bank_details["bank_executed"])
        self.assertTrue(context.vendor_details["created"])
        self.assertTrue(states[-1])
        self.assertTrue(all(status == "completed" for status in states[-1]))


if __name__ == "__main__":
    unittest.main()
