"""Configuration-driven workflow engine for vendor onboarding."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from config_data.country_config import ConfigService
from core.operation_factory import OperationFactory
from core.processing_context import ProcessingContext
from models.country import WorkflowStep
from models.progress import ProgressState
from services.progress_service import ProgressService
from utils.logging import get_logger

UpdateCallback = Callable[[ProgressState], Awaitable[None]]
PauseCallback = Callable[[WorkflowStep, ProcessingContext], Awaitable[bool]]

LOGGER = get_logger(__name__)


class DocumentProcessor:
    """Executes the selected country's configured workflow in order.

    The processor knows only generic workflow step types. Country-specific
    document names, operation names, and sequence are read from
    ``countries.json`` through ``ConfigService``.
    """

    def __init__(
        self,
        config: ConfigService,
        operation_factory: type[OperationFactory] = OperationFactory,
    ) -> None:
        self._config = config
        self._operation_factory = operation_factory

    async def process(
        self,
        country: str,
        uploaded_files: dict[str, str],
        on_update: UpdateCallback,
        on_pause: PauseCallback | None = None,
    ) -> ProcessingContext:
        """Run the configured workflow for a country.

        Args:
            country: Selected country name.
            uploaded_files: Uploaded file references keyed by document type.
            on_update: Callback used to update the existing progress card.
            on_pause: Optional callback for upload/form/review/decision waits.

        Returns:
            The populated processing context.
        """
        workflow = self._config.get_workflow(country)
        progress = ProgressService(self._config.get_process(country))
        context = ProcessingContext(
            selected_country=country, uploaded_files=uploaded_files
        )

        LOGGER.info("Workflow started country=%s steps=%s", country, len(workflow))
        progress.start()
        await on_update(progress.state)

        try:
            for index, step in enumerate(workflow):
                if progress.state.current_index != index:
                    progress.next_step()
                    await on_update(progress.state)
                await self._execute_step(step, context, on_pause)
                progress.complete_step()
                await on_update(progress.state)
            progress.complete()
            await on_update(progress.state)
            LOGGER.info("Workflow completed country=%s", country)
            return context
        except Exception:
            progress.fail()
            await on_update(progress.state)
            LOGGER.exception("Workflow failed country=%s", country)
            raise

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: ProcessingContext,
        on_pause: PauseCallback | None,
    ) -> None:
        start = time.perf_counter()
        LOGGER.info("Step started step_id=%s step_type=%s", step.id, step.type)
        if step.document:
            context.document_type = step.document
            context.uploaded_file = context.uploaded_files.get(step.document)

        if step.type == "operation":
            await self._execute_operation(step, context)
        elif step.type == "upload":
            await self._pause_or_validate_upload(step, context, on_pause)
        elif step.type in {"form", "review", "decision"}:
            await self._pause(step, context, on_pause)
        else:
            raise ValueError(f"Unsupported workflow step type: {step.type}")

        duration = time.perf_counter() - start
        LOGGER.info("Step completed step_id=%s duration=%.3fs", step.id, duration)

    async def _execute_operation(
        self, step: WorkflowStep, context: ProcessingContext
    ) -> None:
        if not step.operation:
            raise ValueError(f"Operation step has no operation: {step.id}")
        service = self._operation_factory.get(step.operation)
        start = time.perf_counter()
        await service.execute(context)
        LOGGER.info(
            "Operation executed operation=%s service=%s duration=%.3fs",
            step.operation,
            service.__class__.__name__,
            time.perf_counter() - start,
        )

    async def _pause_or_validate_upload(
        self,
        step: WorkflowStep,
        context: ProcessingContext,
        on_pause: PauseCallback | None,
    ) -> None:
        if not step.document:
            raise ValueError(f"Upload step has no document: {step.id}")
        if step.document not in context.uploaded_files:
            if not await self._pause(step, context, on_pause):
                raise RuntimeError(f"Waiting for upload: {step.document}")
        context.uploaded_file = context.uploaded_files[step.document]

    async def _pause(
        self,
        step: WorkflowStep,
        context: ProcessingContext,
        on_pause: PauseCallback | None,
    ) -> bool:
        if on_pause is None:
            return True
        return await on_pause(step, context)
