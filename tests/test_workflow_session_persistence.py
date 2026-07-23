import unittest

from config_data.country_config import ConfigService
from flows.vendor_create.document_collector import WorkflowService
from models.workflow import DocumentStatus, WorkflowPhase


class WorkflowSessionPersistenceTests(unittest.TestCase):
    def test_workflow_state_round_trips_through_dict(self) -> None:
        config = ConfigService("config_data/countries.json")
        service = WorkflowService(config)
        service.start_workflow()
        service.select_country("France")
        service.select_operation("Create")
        service.begin_document_collection()
        service.submit_document("/tmp/avis.pdf")

        restored = WorkflowService(config)
        restored.load_dict(service.to_dict())
        state = restored.get_state()

        self.assertEqual(state.phase, WorkflowPhase.PROCESSING)
        self.assertEqual(state.country, "France")
        self.assertEqual(state.current_document, "AVIS")
        self.assertEqual(state.documents["AVIS"].status, DocumentStatus.UPLOADED)
        self.assertEqual(state.documents["AVIS"].files, ["/tmp/avis.pdf"])


if __name__ == "__main__":
    unittest.main()
