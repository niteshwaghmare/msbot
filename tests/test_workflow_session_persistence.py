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


class DefaultSessionSchemaTests(unittest.TestCase):
    def test_default_session_includes_current_workflow_state_shape(self) -> None:
        from services.session_factory import SessionFactory

        session = SessionFactory.create_empty_session()

        self.assertEqual(session["workflow_state"]["phase"], "start")
        self.assertEqual(session["workflow_state"]["workflow_status"], "STARTED")
        self.assertEqual(session["available_countries"], [])
        self.assertEqual(session["available_operations"], [])
        self.assertEqual(session["workflow_state"]["current_workflow_index"], 0)
        self.assertEqual(session["workflow_state"]["documents"], {})
        self.assertFalse(session["workflow_state"]["review_confirmed"])
        self.assertFalse(session["workflow_state"]["vendor_created"])

    def test_restore_session_adds_workflow_state_for_existing_sessions(self) -> None:
        from services.session_factory import SessionFactory

        session = SessionFactory.restore_session({"country": "France"})

        self.assertEqual(session["country"], "France")
        self.assertEqual(session["workflow_state"]["phase"], "start")


class WorkflowControllerSessionSnapshotTests(unittest.TestCase):
    def test_session_snapshot_captures_config_and_workflow_status(self) -> None:
        import sys
        import types

        redis_module = types.ModuleType("redis")
        exceptions_module = types.ModuleType("redis.exceptions")
        exceptions_module.AuthenticationError = RuntimeError
        exceptions_module.ConnectionError = RuntimeError
        redis_module.Redis = object
        redis_module.exceptions = exceptions_module
        sys.modules.setdefault("redis", redis_module)
        sys.modules.setdefault("redis.exceptions", exceptions_module)

        from flows.vendor_create.create_flow import Session, WorkflowController

        config = ConfigService("config_data/countries.json")
        workflow = WorkflowService(config)
        workflow.start_workflow()
        workflow.select_country("France")
        workflow.select_operation("Create")
        workflow.begin_document_collection()

        stored_session: dict[str, object] = {}
        controller = WorkflowController(config)
        controller._sync_session_snapshot(stored_session, Session(workflow))

        self.assertEqual(stored_session["available_countries"], config.get_countries())
        self.assertEqual(stored_session["available_operations"], config.get_operations())
        self.assertEqual(stored_session["country"], "France")
        self.assertEqual(stored_session["country_code"], "FR")
        self.assertEqual(stored_session["currency"], "EUR")
        self.assertEqual(stored_session["workflow"]["stage"], "awaiting_document")
        self.assertEqual(stored_session["workflow"]["current_step"], "process_avis")
        self.assertEqual(stored_session["workflow"]["status"], "WAITING_FOR_DOCUMENT_UPLOAD")
        self.assertEqual(stored_session["documents"]["AVIS"]["status"], "WAITING_FOR_UPLOAD")
        self.assertEqual(stored_session["documents"]["RIB"]["display_name"], "RIB")


if __name__ == "__main__":
    unittest.main()
