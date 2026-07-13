"""Coordinates a single conversation's onboarding session.

WorkflowController is the orchestration layer between the card router
and the services. It owns per-conversation session state, drives each
transition to the correct next card, and runs the simulated processing
with in-place progress-card updates. It contains no card JSON and no
state-machine rules; it composes the services and card builders.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from botbuilder.core import MessageFactory, TurnContext
from botbuilder.schema import Activity

from bot.cards.country_card import CountryCard
from bot.cards.operation_card import OperationCard
from bot.cards.progress_card import ProgressCard
from bot.cards.upload_card import UploadCard
from models.progress import ProgressState
from services.config_service import ConfigService
from services.progress_service import ProgressService
from services.workflow_service import WorkflowService
from models.workflow import WorkflowPhase


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
        session.workflow.select_country(country)
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
        workflow.select_operation(operation)

        if workflow.requires_documents():
            workflow.begin_document_collection()
            card = UploadCard.render(
                workflow.get_documents(),
                workflow.get_state().country,
                workflow.get_current_document(),
                self._is_local_environment(),
            )
            await turn_context.send_activity(MessageFactory.attachment(card))
        else:
            await self._begin_processing(turn_context, session)

    async def handle_submit(
        self, turn_context: TurnContext, payload: dict[str, object] | None = None
    ) -> None:
        """Handle document submission and advance the workflow."""
        session = self._session(turn_context)
        workflow = session.workflow

        if workflow.get_state().phase is not WorkflowPhase.AWAITING_DOCUMENT:
            await turn_context.send_activity(
                "The document step is not active right now."
            )
            return

        document_value = self._extract_document_value(turn_context, payload)
        if not document_value:
            await turn_context.send_activity(
                "Please provide a file path for local runs or upload a document attachment."
            )
            return

        workflow.submit_document(document_value)

        if workflow.get_state().phase is WorkflowPhase.AWAITING_DOCUMENT:
            card = UploadCard.render(
                workflow.get_documents(),
                workflow.get_state().country,
                workflow.get_current_document(),
                self._is_local_environment(),
            )
            await turn_context.send_activity(MessageFactory.attachment(card))
        else:
            await self._begin_processing(turn_context, session)

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

    async def _begin_processing(
        self, turn_context: TurnContext, session: Session
    ) -> None:
        """Transition to processing and run the simulation in the background.

        Sends the initial progress card, captures its activity id for
        in-place updates, then launches the FakeProcessor as a background
        task so the turn returns promptly rather than blocking for the
        full simulation.

        Args:
            turn_context: The current turn context.
            session: The session being processed.
        """
        session.workflow.submit_documents()

        progress_service = ProgressService(self._config.get_process())

        # Send the first progress card and remember its id so every later
        # render updates this same message instead of posting a new one.
        first_card = ProgressCard.render(progress_service.state)
        sent = await turn_context.send_activity(MessageFactory.attachment(first_card))
        session.progress_activity_id = sent.id

        # The processor drives state; this callback re-renders the same
        # card. Captured references let the background task update it after
        # the turn has already returned.
        reference = TurnContext.get_conversation_reference(turn_context.activity)
        adapter = turn_context.adapter

        async def on_update(state: ProgressState) -> None:
            async def _do_update(ctx: TurnContext) -> None:
                card = ProgressCard.render(state)
                activity = MessageFactory.attachment(card)
                activity.id = session.progress_activity_id
                await ctx.update_activity(activity)

            await adapter.continue_conversation(
                reference, _do_update, self._app_id
            )

        # Import here to avoid a circular import at module load time.
        from simulator.fake_processor import FakeProcessor

        processor = FakeProcessor(
            progress_service,
            on_update,
            step_delay_seconds=self._config.step_delay_seconds,
        )

        # Run without blocking the turn. On completion, mark the workflow
        # complete so the session reflects the finished state.
        async def _run_and_finalise() -> None:
            await processor.run()
            session.workflow.complete()

        asyncio.create_task(_run_and_finalise())