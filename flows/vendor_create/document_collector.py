"""Owns a single user's configuration-driven workflow state transitions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from config_data.country_config import ConfigService
from models.country import Country, DocumentConfig, WorkflowStep
from models.workflow import DocumentStatus, DocumentWorkflowState, WaitingFor, WorkflowPhase, WorkflowState


class WorkflowError(Exception):
    """Raised when a workflow transition is invalid."""


_OPERATIONS_REQUIRING_DOCUMENTS: frozenset[str] = frozenset({"Create"})
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class WorkflowService:
    """Maintains one user's onboarding state and workflow cursor."""

    def __init__(self, config: ConfigService) -> None:
        """Initialise the service with a fresh workflow state."""
        self._config = config
        self._state = WorkflowState()

    def start_workflow(self) -> WorkflowState:
        """Reset to the start phase, clearing prior selections."""
        self._state = WorkflowState(phase=WorkflowPhase.START, workflow_status="STARTED")
        return self._state

    def select_country(self, country: str) -> WorkflowState:
        """Record the chosen country and advance the phase."""
        if self._config.get_country(country) is None:
            raise WorkflowError(f"Unknown country: {country}")
        self._state.country = country
        self._state.phase = WorkflowPhase.COUNTRY_SELECTED
        self._state.workflow_status = "WAITING_FOR_OPERATION"
        return self._state

    def select_operation(self, operation: str) -> WorkflowState:
        """Record the chosen operation and prepare workflow state."""
        if self._state.phase is not WorkflowPhase.COUNTRY_SELECTED:
            raise WorkflowError("Select a country before an operation.")
        if operation not in self._config.get_operations():
            raise WorkflowError(f"Unknown operation: {operation}")
        self._state.operation = operation
        self._state.phase = WorkflowPhase.OPERATION_SELECTED
        self._state.current_workflow_index = 0
        self._initialize_document_states()
        return self._state

    def requires_documents(self) -> bool:
        """Whether the selected operation routes into the configured workflow."""
        if self._state.operation is None:
            raise WorkflowError("No operation selected.")
        return self._state.operation in _OPERATIONS_REQUIRING_DOCUMENTS

    def begin_document_collection(self) -> WorkflowState:
        """Start the current document workflow stage and pause for upload."""
        if self._state.phase is not WorkflowPhase.OPERATION_SELECTED:
            raise WorkflowError("Select an operation before collecting documents.")
        return self.start_current_workflow_step()

    def start_current_workflow_step(self) -> WorkflowState:
        """Start the top-level step at the current workflow cursor."""
        step = self.current_step()
        if step.type == "document":
            doc_type = step.document
            if not doc_type:
                raise WorkflowError(f"Document step {step.id} has no document reference.")
            doc_state = self._state.documents.setdefault(doc_type, self._document_state_for(step))
            if doc_state.status is DocumentStatus.COMPLETED:
                self._state.current_workflow_index += 1
                return self.start_current_workflow_step()
            self._state.current_document = doc_type
            doc_state.status = DocumentStatus.WAITING_FOR_UPLOAD
            self._state.phase = WorkflowPhase.AWAITING_DOCUMENT
            self._state.waiting_for = WaitingFor.DOCUMENT_UPLOAD
            self._state.workflow_status = "WAITING_FOR_DOCUMENT_UPLOAD"
            return self._state
        if step.type == "form":
            self._state.phase = WorkflowPhase.AWAITING_FORM
            self._state.waiting_for = WaitingFor.FORM
            self._state.workflow_status = "WAITING_FOR_FORM"
            return self._state
        if step.type == "review":
            self._state.phase = WorkflowPhase.AWAITING_REVIEW
            self._state.waiting_for = WaitingFor.REVIEW
            self._state.workflow_status = "WAITING_FOR_REVIEW"
            return self._state
        if step.type == "operation":
            self._state.phase = WorkflowPhase.CREATING_VENDOR
            self._state.waiting_for = None
            self._state.workflow_status = "CREATING_VENDOR"
            return self._state
        raise WorkflowError(f"Unsupported workflow step type: {step.type}")

    def current_step(self) -> WorkflowStep:
        """Return the current top-level workflow step."""
        country = self._country()
        if self._state.current_workflow_index >= len(country.workflow):
            raise WorkflowError("Workflow is already complete.")
        return country.workflow[self._state.current_workflow_index]

    def current_document_config(self) -> DocumentConfig:
        """Return upload validation metadata for the current document."""
        if not self._state.current_document:
            raise WorkflowError("No current document.")
        document = self._country().get_document(self._state.current_document)
        if document is None:
            raise WorkflowError(f"Unknown document: {self._state.current_document}")
        return document

    def submit_document(self, document_value: str) -> WorkflowState:
        """Validate and store a document upload for the active document stage."""
        if self._state.phase is not WorkflowPhase.AWAITING_DOCUMENT or not self._state.current_document:
            raise WorkflowError("No pending document to submit.")
        document = self.current_document_config()
        ext = Path(document_value).suffix.lower()
        if document.allowed_extensions and ext and ext not in document.allowed_extensions:
            raise WorkflowError(f"Unsupported file type for {document.document_type}: {ext}")
        doc_state = self._state.documents[self._state.current_document]
        if doc_state.files and not document.allow_multiple:
            return self._state
        files = [document_value]
        if len(files) < document.min_files or len(files) > document.max_files:
            raise WorkflowError(f"Invalid file count for {document.document_type}.")
        doc_state.files = files
        doc_state.status = DocumentStatus.UPLOADED
        self._state.collected_documents.append(document_value)
        self._state.phase = WorkflowPhase.PROCESSING
        self._state.waiting_for = None
        self._state.workflow_status = "PROCESSING_DOCUMENT"
        return self._state

    def complete_document(self) -> WorkflowState:
        """Mark active document complete and advance to the next top-level step."""
        if not self._state.current_document:
            raise WorkflowError("No current document to complete.")
        self._state.documents[self._state.current_document].status = DocumentStatus.COMPLETED
        self._state.current_document = None
        self._state.current_workflow_index += 1
        return self.start_current_workflow_step()

    def fail_document(self, message: str) -> WorkflowState:
        """Mark active document and workflow failed with a safe error message."""
        if self._state.current_document:
            doc = self._state.documents[self._state.current_document]
            doc.status = DocumentStatus.FAILED
            doc.error_message = message
        self._state.phase = WorkflowPhase.FAILED
        self._state.workflow_status = "FAILED"
        self._state.waiting_for = None
        return self._state

    def submit_form(self, payload: dict[str, Any]) -> list[str]:
        """Validate configured form fields, store values, and advance to review."""
        step = self.current_step()
        if self._state.phase is not WorkflowPhase.AWAITING_FORM or payload.get("workflowStepId") != step.id:
            return []
        errors: list[str] = []
        values: dict[str, str | None] = {}
        for field in step.raw.get("fields", []):
            field_id = field["id"]
            value = str(payload.get(field_id, "")).strip()
            values[field_id] = value
            if field.get("required") and not value:
                errors.append(f"{field.get('label', field_id)} is required.")
            if value and field.get("type") == "email" and not _EMAIL_RE.match(value):
                errors.append(f"{field.get('label', field_id)} must be a valid email address.")
            validation = field.get("validation", {})
            if value and len(value) < int(validation.get("minLength", 0)):
                errors.append(f"{field.get('label', field_id)} is too short.")
            if value and "maxLength" in validation and len(value) > int(validation["maxLength"]):
                errors.append(f"{field.get('label', field_id)} is too long.")
        if errors:
            return errors
        if self._state.waiting_for is WaitingFor.FORM:
            self._state.form_data.update(values)
            self._state.current_workflow_index += 1
            self._state.waiting_for = None
            self.start_current_workflow_step()
        return []

    def confirm_review(self) -> bool:
        """Mark review confirmed and advance once, returning False for retries."""
        if self._state.review_confirmed:
            return False
        step = self.current_step()
        if self._state.phase is not WorkflowPhase.AWAITING_REVIEW or step.type != "review":
            return False
        self._state.review_confirmed = True
        self._state.current_workflow_index += 1
        self._state.waiting_for = None
        self.start_current_workflow_step()
        return True

    def edit_form(self) -> WorkflowState:
        """Move back to the configured vendor-information form without resetting documents."""
        country = self._country()
        for index, step in enumerate(country.workflow):
            if step.type == "form":
                self._state.current_workflow_index = index
                self._state.review_confirmed = False
                return self.start_current_workflow_step()
        raise WorkflowError("No form step configured.")

    def complete(self) -> WorkflowState:
        """Mark the workflow finished."""
        self._state.phase = WorkflowPhase.COMPLETED
        self._state.workflow_status = "COMPLETED"
        self._state.waiting_for = None
        return self._state

    def mark_vendor_created(self) -> bool:
        """Mark vendor creation executed, returning False if already executed."""
        if self._state.vendor_created:
            return False
        self._state.vendor_created = True
        return True

    def get_state(self) -> WorkflowState:
        """Return the current workflow state."""
        return self._state

    def get_documents(self) -> list[str]:
        """Return document types for selected country metadata only."""
        return self._country().document_types

    def get_current_document(self) -> str:
        """Return the document currently waiting for input."""
        if self._state.current_document is None:
            raise WorkflowError("No document is pending.")
        return self._state.current_document

    def _initialize_document_states(self) -> None:
        self._state.documents.clear()
        self._state.form_data.clear()
        for step in self._country().workflow:
            if step.type == "document" and step.document:
                self._state.documents[step.document] = self._document_state_for(step)
            if step.type == "form":
                for field in step.raw.get("fields", []):
                    self._state.form_data.setdefault(field["id"], None)

    @staticmethod
    def _document_state_for(step: WorkflowStep) -> DocumentWorkflowState:
        return DocumentWorkflowState(steps={nested["id"]: "PENDING" for nested in step.raw.get("steps", [])})

    def _country(self) -> Country:
        if self._state.country is None:
            raise WorkflowError("No country selected.")
        country = self._config.get_country(self._state.country)
        if country is None:
            raise WorkflowError(f"Unknown country: {self._state.country}")
        return country
