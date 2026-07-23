# Vendor Create Flow

This flow implements the core vendor onboarding path for the demo bot.

## Purpose

The `vendor_create` flow guides the user through a multi-step onboarding process, including:

1. Country selection
2. Operation selection
3. Document collection (for operations that require documents)
4. Processing progress simulation

## Key components

- `create_flow.py`
  - `WorkflowController`: orchestrates the conversation for each user session.
  - Maintains per-conversation `Session` state.
  - Sends Adaptive Card attachments and transitions users through the flow.

- `document_collector.py`
  - `WorkflowService`: owns the workflow state machine and valid transitions.
  - Handles select country, select operation, begin document collection, submit document, and complete processing.

- `details_form.py` and `review.py`
  - Placeholder modules for later details and review steps.

## Flow behavior

- The router sends card submit payloads into the controller.
- `show_countries()` starts or restarts the onboarding flow.
- After country selection, the user sees the operation card.
- If the selected operation requires documents, the flow begins document collection.
- Documents are collected one-by-one, and after the final document the flow moves to processing.
- The processing step sends a progress card and updates it asynchronously.

## Implementation notes

- The flow uses `ConfigService` to validate countries, operations, and required documents.
- Document collection is currently only required for operations in `_OPERATIONS_REQUIRING_DOCUMENTS`.
- Session state is persisted through `services.session_service` using Redis-backed storage.
- The processing path uses `ProgressService` and `processors.vendor_processor.FakeProcessor`.
