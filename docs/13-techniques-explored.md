# 13 - Techniques Explored

## Configuration-Driven Workflow

- **Problem:** Country rules vary.
- **Approach:** Store countries, documents, forms, and workflow steps in JSON and load them with `ConfigService`.
- **Benefit:** Less hardcoded country branching.
- **Limitation:** Some configured legacy step types are not fully active in the current conversation path.
- **Future improvement:** Version and validate the schema more strictly.

## Sequential Document Processing

- **Problem:** Users need clear guidance and immediate feedback.
- **Approach:** Request and process one top-level document stage before asking for the next.
- **Benefit:** Easier state management and clearer progress cards.
- **Limitation:** Not optimized for bulk upload.
- **Future improvement:** Add optional parallel/batch mode when business rules allow it.

## Dynamic Adaptive Cards

- **Problem:** Cards change based on countries and form config.
- **Approach:** Builder classes render cards from config and state.
- **Benefit:** UI is consistent and reusable.
- **Limitation:** No template files or snapshot tests yet.
- **Future improvement:** Add card JSON snapshot tests.

## Progress Card Mutation

- **Problem:** Repeated status messages clutter chat.
- **Approach:** Store sent activity ID and call `update_activity()`.
- **Benefit:** One live progress card per document.
- **Limitation:** Deleted/expired messages are not handled specifically.
- **Future improvement:** Fall back to sending a new card when update fails.

## Pause-and-Resume Processing

- **Problem:** Bot turns are event-driven.
- **Approach:** Persist cursor and waiting status in `WorkflowState` between activities.
- **Benefit:** The bot knows what it is waiting for on each new turn.
- **Limitation:** State is in memory only.
- **Future improvement:** Use durable storage and concurrency control.

## Polymorphic Operations and Factory Resolution

- **Problem:** Config references operations by name.
- **Approach:** Use `BaseOperation` implementations selected by `OperationFactory`.
- **Benefit:** New operations can be added without rewriting orchestration.
- **Limitation:** Static singleton instances limit runtime configuration.
- **Future improvement:** Inject service instances with real clients and settings.

## Server-Side Validation

- **Problem:** Client-side card validation is not authoritative.
- **Approach:** `WorkflowService.submit_form()` validates payloads and `submit_document()` validates uploads.
- **Benefit:** Safer state transitions.
- **Limitation:** Validation is basic.
- **Future improvement:** Add country-specific validators and PII-safe error reporting.

## Idempotent Activity Handling

- **Problem:** Teams can retry or users can click twice.
- **Approach:** Check completed steps, `review_confirmed`, and `vendor_created` flags.
- **Benefit:** Reduces duplicate processing.
- **Limitation:** No distributed locks.
- **Future improvement:** Persist idempotency keys and use optimistic concurrency.

## Mock-First Development

- **Problem:** UI/orchestration can be built before backend services exist.
- **Approach:** Mock services update context with simple completion results.
- **Benefit:** Fast demo and test feedback.
- **Limitation:** Does not prove real API behavior.
- **Future improvement:** Add interfaces/fakes and contract tests for real integrations.
