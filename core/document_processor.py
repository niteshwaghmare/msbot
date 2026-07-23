"""Configuration-driven document workflow processor."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from core.operation_factory import OperationFactory
from models.country import WorkflowStep
from models.progress import ProgressState
from services.progress_service import ProgressService
from core.logging import get_logger

LOGGER = get_logger(__name__)
UpdateCallback = Callable[[ProgressState], Awaitable[None]]


@dataclass
class ProcessingContext:
    """Shared mutable state passed to every workflow operation.

    Operations enrich this object instead of exchanging long parameter lists.
    The fields are intentionally generic so country behavior remains in
    configuration and operation implementations, not in the processor.
    """

    selected_country: str
    uploaded_files: dict[str, str] = field(default_factory=dict)
    document_type: str | None = None
    uploaded_file: str | None = None
    ocr_result: dict[str, Any] = field(default_factory=dict)
    extracted_fields: dict[str, Any] = field(default_factory=dict)
    validation_result: dict[str, Any] = field(default_factory=dict)
    bank_details: dict[str, Any] = field(default_factory=dict)
    tax_details: dict[str, Any] = field(default_factory=dict)
    vendor_details: dict[str, Any] = field(default_factory=dict)
    duplicate_check_result: dict[str, Any] = field(default_factory=dict)
    workflow_data: dict[str, Any] = field(default_factory=dict)
    terminated: bool = False
    error_message: str | None = None


class DocumentProcessor:
    """Runs the selected country's configured workflow sequentially."""

    def __init__(
        self,
        workflow: list[WorkflowStep],
        progress: ProgressService,
        on_update: UpdateCallback,
        operation_factory: type[OperationFactory] = OperationFactory,
    ) -> None:
        self._workflow = workflow
        self._progress = progress
        self._on_update = on_update
        self._operation_factory = operation_factory

    async def run(self, context: ProcessingContext) -> ProcessingContext:
        """Execute all configured workflow steps in order."""
        LOGGER.info("Workflow started country=%s", context.selected_country)
        self._progress.start()
        await self._emit()

        for index, step in enumerate(self._workflow):
            start = time.perf_counter()
            try:
                LOGGER.info("Step started step_id=%s step_type=%s", step.id, step.type)
                await self._execute_step(step, context)
                if context.terminated:
                    LOGGER.info("Workflow terminated step_id=%s", step.id)
                    break
                self._progress.complete_step()
                await self._emit()
                duration = time.perf_counter() - start
                LOGGER.info("Step completed step_id=%s duration=%.3fs", step.id, duration)
            except Exception as error:  # noqa: BLE001 - log and stop workflow cleanly.
                context.error_message = (
                    "Sorry, something went wrong while processing your onboarding workflow. "
                    "Please try again or contact support."
                )
                self._progress.fail()
                await self._emit()
                LOGGER.exception("Workflow error step_id=%s error=%s", step.id, error)
                return context

            if index < len(self._workflow) - 1:
                self._progress.next_step()
                await self._emit()

        if not context.terminated and not self._progress.state.has_failed:
            self._progress.complete()
            await self._emit()
            LOGGER.info("Workflow completed country=%s", context.selected_country)
        return context

    async def _execute_step(self, step: WorkflowStep, context: ProcessingContext) -> None:
        """Dispatch a configured step without country-specific branching."""
        if step.type == "operation":
            await self._execute_operation(step, context)
            return
        if step.type == "decision":
            await self._execute_decision(step, context)
            return
        if step.type == "upload":
            self._load_uploaded_document(step, context)
            return
        if step.type in {"form", "review"}:
            context.workflow_data[step.id] = step.raw
            return
        raise ValueError(f"Unsupported workflow step type: {step.type}")

    async def _execute_operation(self, step: WorkflowStep, context: ProcessingContext) -> None:
        operation_name = step.operation
        if not operation_name:
            raise ValueError(f"Operation step {step.id} has no operation name.")
        service = self._operation_factory.get(operation_name)
        start = time.perf_counter()
        updated_context = await service.execute(context)
        if updated_context is not None:
            # Services should return the same context, but accepting an equivalent
            # object keeps the BaseOperation contract flexible.
            context.__dict__.update(updated_context.__dict__)
        LOGGER.info(
            "Operation executed operation=%s service=%s duration=%.3fs",
            operation_name,
            service.__class__.__name__,
            time.perf_counter() - start,
        )

    async def _execute_decision(self, step: WorkflowStep, context: ProcessingContext) -> None:
        if step.operation:
            await self._execute_operation(step, context)
        duplicate_found = bool(context.duplicate_check_result.get("duplicate_found"))
        user_decision = str(context.workflow_data.get(step.id, "continue")).lower()
        if duplicate_found and user_decision == "cancel":
            context.terminated = True

    def _load_uploaded_document(self, step: WorkflowStep, context: ProcessingContext) -> None:
        document_type = step.document
        if not document_type:
            raise ValueError(f"Upload step {step.id} has no document type.")
        uploaded_file = context.uploaded_files.get(document_type)
        if not uploaded_file:
            raise ValueError(f"Missing upload for document type {document_type}.")
        context.document_type = document_type
        context.uploaded_file = uploaded_file

    async def _emit(self) -> None:
        await self._on_update(self._progress.state)
