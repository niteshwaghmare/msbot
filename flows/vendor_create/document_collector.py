"""Owns a single user's workflow state and its transitions.

WorkflowService is the conversation state machine. It validates each
user selection against configuration and advances the WorkflowState
through its phases. It holds no rendering or processing logic; it only
records where the user is and what they have chosen.
"""

from __future__ import annotations

from models.workflow import WorkflowState, WorkflowPhase
from config_data.country_config import ConfigService


class WorkflowError(Exception):
    """Raised when a workflow transition is invalid."""


# --- Operation routing -----------------------------------------------------
# Phase 1 infers which operations require a document upload. Only "Create"
# collects documents; the other operations route straight to processing.
# This is the single place that assumption lives. When Phase 2 enriches the
# config (e.g. a `requires_documents` flag per operation), replace the body
# of `requires_documents()` below and nothing else changes.
_OPERATIONS_REQUIRING_DOCUMENTS: frozenset[str] = frozenset({"Create"})


class WorkflowService:
    """Maintains and transitions one user's onboarding state.

    Each instance corresponds to a single user's session. Selections are
    validated against the injected ConfigService so invalid button input
    cannot move the state into an inconsistent phase.
    """

    def __init__(self, config: ConfigService) -> None:
        """Initialise the service with a fresh workflow state.

        Args:
            config: The configuration service used to validate country
                and operation selections.
        """
        self._config = config
        self._state = WorkflowState()

    def start_workflow(self) -> WorkflowState:
        """Reset to the start phase, clearing any prior selections.

        Returns:
            The reset workflow state.
        """
        self._state = WorkflowState(phase=WorkflowPhase.START)
        return self._state

    def select_country(self, country: str) -> WorkflowState:
        """Record the chosen country and advance the phase.

        Args:
            country: The country display name selected by the user.

        Returns:
            The updated workflow state.

        Raises:
            WorkflowError: If the country is not configured.
        """
        if self._config.get_country(country) is None:
            raise WorkflowError(f"Unknown country: {country}")
        self._state.country = country
        self._state.phase = WorkflowPhase.COUNTRY_SELECTED
        return self._state

    def select_operation(self, operation: str) -> WorkflowState:
        """Record the chosen operation and advance the phase.

        Args:
            operation: The operation label selected by the user.

        Returns:
            The updated workflow state.

        Raises:
            WorkflowError: If no country was selected first, or the
                operation is not configured.
        """
        if self._state.phase is not WorkflowPhase.COUNTRY_SELECTED:
            raise WorkflowError("Select a country before an operation.")
        resolved_operation = self._config.resolve_operation(operation)
        if resolved_operation is None:
            raise WorkflowError(f"Unknown operation: {operation}")
        self._state.operation = resolved_operation
        self._state.phase = WorkflowPhase.OPERATION_SELECTED
        return self._state

    def requires_documents(self) -> bool:
        """Whether the selected operation collects documents.

        Returns:
            True if the current operation routes to a document upload
            step; False if it proceeds straight to processing.

        Raises:
            WorkflowError: If no operation has been selected yet.
        """
        if self._state.operation is None:
            raise WorkflowError("No operation selected.")
        return self._state.operation in _OPERATIONS_REQUIRING_DOCUMENTS

    def begin_document_collection(self) -> WorkflowState:
        """Start collecting required documents one at a time."""
        if self._state.phase is not WorkflowPhase.OPERATION_SELECTED:
            raise WorkflowError("Select an operation before collecting documents.")
        if not self.requires_documents():
            raise WorkflowError("Selected operation does not require documents.")

        self._state.collected_documents = []
        self._state.current_document = self.get_documents()[0]
        self._state.phase = WorkflowPhase.AWAITING_DOCUMENT
        return self._state

    def get_current_document(self) -> str:
        """Return the document currently waiting for input."""
        if self._state.current_document is None:
            raise WorkflowError("No document is pending.")
        return self._state.current_document

    def submit_document(self, document_value: str) -> WorkflowState:
        """Store one document response and advance to the next document or processing."""
        if self._state.phase is not WorkflowPhase.AWAITING_DOCUMENT:
            raise WorkflowError("No pending document to submit.")
        if self._state.current_document is None:
            raise WorkflowError("No pending document to submit.")

        self._state.collected_documents.append(document_value)
        documents = self.get_documents()
        current_index = documents.index(self._state.current_document)

        if current_index + 1 < len(documents):
            self._state.current_document = documents[current_index + 1]
            self._state.phase = WorkflowPhase.AWAITING_DOCUMENT
        else:
            self._state.current_document = None
            self._state.phase = WorkflowPhase.PROCESSING

        return self._state

    def submit_documents(self) -> WorkflowState:
        """Advance from operation/upload into the processing phase."""
        if self._state.phase is WorkflowPhase.PROCESSING:
            return self._state
        if self._state.phase is not WorkflowPhase.OPERATION_SELECTED:
            raise WorkflowError("Select an operation before submitting.")
        self._state.phase = WorkflowPhase.PROCESSING
        return self._state

    def complete(self) -> WorkflowState:
        """Mark the workflow finished after processing.

        Returns:
            The updated workflow state, now in the COMPLETED phase.

        Raises:
            WorkflowError: If called outside the processing phase.
        """
        if self._state.phase is not WorkflowPhase.PROCESSING:
            raise WorkflowError("Can only complete from processing.")
        self._state.phase = WorkflowPhase.COMPLETED
        return self._state

    def get_state(self) -> WorkflowState:
        """Return the current workflow state.

        Returns:
            The current WorkflowState.
        """
        return self._state

    def get_documents(self) -> list[str]:
        """Return the documents required for the selected country.

        Returns:
            The document types for the currently selected country.

        Raises:
            WorkflowError: If no country has been selected.
        """
        if self._state.country is None:
            raise WorkflowError("No country selected.")
        return self._config.get_documents(self._state.country)