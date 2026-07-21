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
        self.assertEqual(self.service.get_current_document(), "RBIS")

        self.service.submit_document("/tmp/rbis.pdf")
        state = self.service.get_state()
        self.assertEqual(state.phase, WorkflowPhase.AWAITING_DOCUMENT)
        self.assertEqual(self.service.get_current_document(), "AVIS")

        self.service.submit_document("/tmp/avis.pdf")
        state = self.service.get_state()
        self.assertEqual(state.phase, WorkflowPhase.PROCESSING)
        self.assertEqual(state.collected_documents, ["/tmp/rbis.pdf", "/tmp/avis.pdf"])

    def test_submit_document_requires_active_document_step(self) -> None:
        self.service.start_workflow()
        self.service.select_country("France")
        self.service.select_operation("Create")

        with self.assertRaises(WorkflowError):
            self.service.submit_document("/tmp/rbis.pdf")


if __name__ == "__main__":
    unittest.main()
