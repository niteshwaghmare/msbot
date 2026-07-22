# 07 - State Management

## Actual State Mechanism

The active implementation does not use Bot Framework `ConversationState`, `UserState`, `MemoryStorage`, Redis, or database storage. Instead, `WorkflowController` keeps a process-local dictionary: `dict[conversation_id, Session]`. Each `Session` contains a `WorkflowService` and an unused controller-level `progress_activity_id`; document progress IDs are stored inside `DocumentWorkflowState`.

## Workflow State Objects

`WorkflowState` contains:

- `phase`: high-level `WorkflowPhase`.
- `country` and `operation`.
- `current_workflow_index` and `current_document`.
- `workflow_status` string such as `WAITING_FOR_DOCUMENT_UPLOAD`, `PROCESSING_DOCUMENT`, `WAITING_FOR_FORM`, `WAITING_FOR_REVIEW`, `CREATING_VENDOR`, `COMPLETED`, `FAILED`.
- `waiting_for`: `DOCUMENT_UPLOAD`, `FORM`, or `REVIEW`.
- `documents`: map of document type to `DocumentWorkflowState`.
- `form_data`, `review_confirmed`, and `vendor_created`.

`DocumentWorkflowState` stores lifecycle status, uploaded file values, progress activity ID, current nested step index, per-step statuses, result snapshots, and error messages.

## Conversation State vs User State

Bot Framework conversation state is normally scoped to a conversation thread; user state is scoped to a user across conversations. This project currently emulates conversation state with a Python dictionary keyed by `turn_context.activity.conversation.id`. It does not persist user profile data separately.

## Persistence After Each Turn

Because the sessions dictionary is mutable and in memory, state changes are immediately available to later turns handled by the same Python process. There is no explicit `save_changes()` call because Bot Framework state objects are not used.

## Current Limitations

- State is lost on restart.
- State is not shared across multiple bot instances.
- Concurrent duplicate activities can race because there is no distributed lock.
- Activity IDs for progress cards are useful only while the message still exists and the channel allows updates.

## Idempotency

Implemented guards:

- Re-submitting a document when `allowMultiple` is false returns without adding a second file.
- Completed nested document steps are skipped when processing resumes.
- `confirm_review()` returns `False` on repeated confirmation.
- `mark_vendor_created()` returns `False` after vendor creation was already marked.
- Edit returns only to the form step and does not reset completed documents.

## Production Recommendations

Use durable state storage such as Azure Blob Storage, Cosmos DB, Redis, or SQL. Add optimistic concurrency or locks around review confirmation and vendor creation. Persist conversation references and progress-card activity IDs if background workers or proactive updates are introduced.
