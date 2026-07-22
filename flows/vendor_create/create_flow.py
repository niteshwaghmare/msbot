"""Coordinates a single conversation's onboarding session.

WorkflowController is the orchestration layer between the card router
and the services. It owns per-conversation session state, drives each
transition to the correct next card, and runs the simulated processing
with in-place progress-card updates. It contains no card JSON and no
state-machine rules; it composes the services and card builders.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from botbuilder.core import MessageFactory, TurnContext

from cards.country_select_card import CountryCard
from cards.operation_card import OperationCard
from cards.progress_card import ProgressCard
from cards.document_upload_card import UploadCard
from cards.details_form_card import DetailsFormCard
from cards.review_card import ReviewCard
from models.progress import ProgressState, StepStatus
from config_data.country_config import ConfigService
from services.progress_service import ProgressService
from flows.vendor_create.document_collector import WorkflowService, WorkflowError
from models.workflow import WorkflowPhase
from utils.logging import activity_log_details, get_logger
from core.operation_factory import OperationFactory
from core.document_processor import ProcessingContext
from models.workflow import DocumentStatus


LOGGER = get_logger(__name__)


@dataclass
class Session:
    """Per-conversation session state.

    Attributes:
        workflow: The workflow state machine for this conversation.
        progress_activity_id: Id of the sent progress card, used to
            update it in place. None until processing begins.
    """

    workflow: WorkflowService
    progress_activity_id: str | None = None


class WorkflowController:
    """Orchestrates onboarding sessions across conversations.

    One controller serves all conversations; per-conversation state is
    isolated in a Session keyed by conversation id. Session storage is
    in-memory for Phase 1 and is the single point to swap for Redis or a
    database in Phase 2.
    """
    def __init__(self, config: ConfigService, app_id: str = "") -> None:
            """Initialise the controller.

            Args:
                config: The shared configuration service.
                app_id: The bot's Microsoft App Id, required to resume a
                    conversation from a background task. Empty is valid for
                    the local Emulator.
            """
            self._config = config
            self._app_id = app_id
            # Phase 2: replace this dict with a distributed/persistent store.
            self._sessions: dict[str, Session] = {}
    # --- Session management ------------------------------------------------

    def _session(self, turn_context: TurnContext) -> Session:
        """Return the session for this conversation, creating it if new.

        Args:
            turn_context: The current turn context.

        Returns:
            The Session for the conversation.
        """
        conversation_id = turn_context.activity.conversation.id
        session = self._sessions.get(conversation_id)
        if session is None:
            session = Session(workflow=WorkflowService(self._config))
            self._sessions[conversation_id] = session
            LOGGER.info(
                "Created workflow session",
                extra=activity_log_details(turn_context),
            )
        return session

    @staticmethod
    def _is_local_environment() -> bool:
        """Return True when the bot is running in a local/dev environment."""
        environment = os.getenv("ENVIRONMENT", "local").strip().lower()
        return environment in {"local", "development", "dev", "test"}

    # --- Flow steps --------------------------------------------------------

    async def show_countries(self, turn_context: TurnContext) -> None:
        """Start (or restart) the flow by showing the country card.

        Args:
            turn_context: The current turn context.
        """
        session = self._session(turn_context)
        LOGGER.info(
            "Showing country selection",
            extra=activity_log_details(turn_context),
        )
        session.workflow.start_workflow()
        session.progress_activity_id = None
        card = CountryCard.render(self._config.get_countries())
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def handle_country(self, turn_context: TurnContext, country: str) -> None:
        """Record the country and show the operation card.

        Args:
            turn_context: The current turn context.
            country: The selected country name.
        """
        session = self._session(turn_context)
        LOGGER.info(
            "Country selected country=%s",
            country,
            extra=activity_log_details(turn_context),
        )
        session.workflow.select_country(country)
        await turn_context.send_activity(
            MessageFactory.text(f"Country selected: {country}")
        )
        card = OperationCard.render(self._config.get_operations(), country)
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def handle_operation(
        self, turn_context: TurnContext, operation: str
    ) -> None:
        """Record the operation and branch to upload or processing.

        Operations requiring documents show the upload card; others go
        straight to processing.

        Args:
            turn_context: The current turn context.
            operation: The selected operation label.
        """
        session = self._session(turn_context)
        workflow = session.workflow
        LOGGER.info(
            "Operation selected operation=%s",
            operation,
            extra=activity_log_details(turn_context),
        )
        workflow.select_operation(operation)
        await turn_context.send_activity(
            MessageFactory.text(f"Operation selected: {operation}")
        )

        if workflow.requires_documents():
            workflow.begin_document_collection()
            await self._send_current_step(turn_context, session)
        else:
            await self._begin_processing(turn_context, session)

    async def handle_submit(
        self, turn_context: TurnContext, payload: dict[str, object] | None = None
    ) -> None:
        """Handle document upload and run that document before advancing."""
        session = self._session(turn_context)
        workflow = session.workflow
        if workflow.get_state().phase is not WorkflowPhase.AWAITING_DOCUMENT:
            await turn_context.send_activity("The document step is not active right now.")
            return
        document_value = self._extract_document_value(turn_context, payload)
        if not document_value:
            await turn_context.send_activity("Please provide a file path for local runs or upload a document attachment.")
            return
        try:
            workflow.submit_document(document_value)
        except WorkflowError as error:
            await turn_context.send_activity(str(error))
            return
        await self._process_current_document(turn_context, session)
        await self._send_current_step(turn_context, session)

    async def handle_vendor_information(
        self, turn_context: TurnContext, payload: dict[str, object]
    ) -> None:
        """Validate and store configured vendor-information fields."""
        session = self._session(turn_context)
        errors = session.workflow.submit_form(payload)
        if errors:
            step = session.workflow.current_step().raw
            card = DetailsFormCard.render(step, session.workflow.get_state().form_data, errors)
            await turn_context.send_activity(MessageFactory.attachment(card))
            return
        await self._send_current_step(turn_context, session)

    async def handle_review_action(
        self, turn_context: TurnContext, payload: dict[str, object]
    ) -> None:
        """Handle review confirmation or edit-information requests."""
        session = self._session(turn_context)
        action = payload.get("action")
        if action == "edit_vendor_information":
            session.workflow.edit_form()
            await self._send_current_step(turn_context, session)
            return
        if action == "confirm_vendor" and session.workflow.confirm_review():
            await self._execute_vendor_creation(turn_context, session)
            return
        await turn_context.send_activity("That review action is no longer active.")

    def _extract_document_value(
        self, turn_context: TurnContext, payload: dict[str, object] | None
    ) -> str | None:
        """Extract the document value from card payload, plain text, or attachments."""
        if payload:
            document_value = payload.get("document_path") or payload.get("document")
            if document_value:
                return str(document_value)

        text = (turn_context.activity.text or "").strip()
        if text:
            return text

        if turn_context.activity.attachments:
            attachment = turn_context.activity.attachments[0]
            return attachment.name or attachment.content_url or "uploaded_attachment"

        return None

    # --- Processing --------------------------------------------------------

    async def _begin_processing(self, turn_context: TurnContext, session: Session) -> None:
        """Run a non-document operation path through the current workflow."""
        await self._execute_vendor_creation(turn_context, session)

    async def _send_current_step(self, turn_context: TurnContext, session: Session) -> None:
        """Render the card for the current top-level workflow step and then pause."""
        step = session.workflow.current_step()
        state = session.workflow.get_state()
        if step.type == "document":
            card = UploadCard.render([step.document or "document"], state.country or "", step.document, self._is_local_environment(), step.raw.get("upload", {}))
            await turn_context.send_activity(MessageFactory.attachment(card))
            return
        if step.type == "form":
            card = DetailsFormCard.render(step.raw, state.form_data)
            await turn_context.send_activity(MessageFactory.attachment(card))
            return
        if step.type == "review":
            card = ReviewCard.render(step.raw, state)
            await turn_context.send_activity(MessageFactory.attachment(card))
            return
        if step.type == "operation":
            await self._execute_vendor_creation(turn_context, session)

    async def _process_current_document(self, turn_context: TurnContext, session: Session) -> None:
        """Run the active document stage's nested steps sequentially."""
        state = session.workflow.get_state()
        document_type = state.current_document
        if not document_type:
            return
        workflow_step = session.workflow.current_step()
        document_state = state.documents[document_type]
        document_state.status = DocumentStatus.PROCESSING
        progress_service = ProgressService([type(workflow_step)(id=s["id"], title=s["title"], type=s["type"], operation=s.get("operation"), document=document_type, raw=dict(s)) for s in workflow_step.raw.get("steps", [])])
        progress_service.start()
        for progress_step in progress_service.state.steps:
            if document_state.steps.get(progress_step.id) == "COMPLETED":
                progress_step.status = StepStatus.COMPLETED
        title = workflow_step.raw.get("progressCard", {}).get("title")
        if not document_state.progress_activity_id:
            sent = await turn_context.send_activity(MessageFactory.attachment(ProgressCard.render(progress_service.state, title)))
            document_state.progress_activity_id = sent.id
        await self._update_progress_card(turn_context, document_state.progress_activity_id, progress_service.state, title)
        context = ProcessingContext(selected_country=state.country or "", uploaded_files={document_type: document_state.files[0]}, document_type=document_type, uploaded_file=document_state.files[0])
        for index, nested in enumerate(workflow_step.raw.get("steps", [])):
            if document_state.steps.get(nested["id"]) == "COMPLETED":
                continue
            progress_service.state.current_index = index
            progress_service.state.steps[index].status = StepStatus.RUNNING
            document_state.current_step_index = index
            document_state.steps[nested["id"]] = "IN_PROGRESS"
            await self._update_progress_card(turn_context, document_state.progress_activity_id, progress_service.state, title)
            try:
                operation = OperationFactory.get(nested["operation"])
                result = await operation.execute(context)
                if result is not None:
                    context = result
                document_state.results[nested["id"]] = self._operation_result(context, nested["operation"])
                document_state.steps[nested["id"]] = "COMPLETED"
                progress_service.state.steps[index].status = StepStatus.COMPLETED
                await self._update_progress_card(turn_context, document_state.progress_activity_id, progress_service.state, title)
            except Exception as error:
                LOGGER.exception("Document operation failed step_id=%s", nested.get("id"))
                document_state.steps[nested["id"]] = "FAILED"
                progress_service.state.steps[index].status = StepStatus.FAILED
                session.workflow.fail_document("Document processing failed. Please try again or contact support.")
                await self._update_progress_card(turn_context, document_state.progress_activity_id, progress_service.state, title)
                await turn_context.send_activity("Document processing failed. Please try again or contact support.")
                return
        progress_service.complete()
        await self._update_progress_card(turn_context, document_state.progress_activity_id, progress_service.state, title)
        session.workflow.complete_document()

    async def _update_progress_card(self, turn_context: TurnContext, activity_id: str | None, state: ProgressState, title: str | None) -> None:
        """Update an existing progress activity in place."""
        if not activity_id:
            return
        activity = MessageFactory.attachment(ProgressCard.render(state, title))
        activity.id = activity_id
        await turn_context.update_activity(activity)

    async def _execute_vendor_creation(self, turn_context: TurnContext, session: Session) -> None:
        """Execute CREATE_VENDOR once through the operation factory."""
        if not session.workflow.mark_vendor_created():
            await turn_context.send_activity("Vendor creation was already completed.")
            return
        step = session.workflow.current_step()
        context = ProcessingContext(selected_country=session.workflow.get_state().country or "")
        await OperationFactory.get(step.operation or "CREATE_VENDOR").execute(context)
        session.workflow.complete()
        await turn_context.send_activity("Vendor created successfully.")

    @staticmethod
    def _operation_result(context: ProcessingContext, operation_name: str) -> object:
        """Return the relevant non-sensitive operation result snapshot."""
        return {
            "OCR": context.ocr_result,
            "VALIDATION": context.validation_result,
            "SIRET": context.tax_details,
            "TIN": context.tax_details,
            "BANK": context.bank_details,
            "GST": context.tax_details,
            "DUPLICATE_CHECK": context.duplicate_check_result,
        }.get(operation_name, context.workflow_data)
