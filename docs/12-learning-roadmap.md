# 12 - Learning Roadmap

## Level 1: Python Foundations

- **Learn:** async/await, type hints, dataclasses, enums, ABCs, exceptions, logging, dependency management, unittest/pytest.
- **Why:** The bot is asynchronous and model-driven.
- **Project link:** `WorkflowState`, `BaseOperation`, `ProcessingContext`, service `execute()` methods.
- **Exercise:** Add a mock operation that writes a value to `ProcessingContext.workflow_data` and test it.

## Level 2: Microsoft Bot Framework Fundamentals

- **Learn:** adapter, `TurnContext`, `Activity`, `ActivityHandler`, message activities, Emulator.
- **Why:** Every user action enters through Bot Framework activities.
- **Project link:** `app.py` and `DemoActivityHandler.on_message_activity()`.
- **Exercise:** Log activity text, value presence, and attachment count for a test message.

## Level 3: Microsoft Teams Bot Fundamentals

- **Learn:** Teams channel behavior, app registration, manifest, installation scopes, conversation references, proactive messages.
- **Why:** Teams card submits and updates behave differently from plain chat messages.
- **Project link:** Adaptive Card submits arrive in `activity.value`; progress cards need activity IDs.
- **Exercise:** Test country selection in Teams App Test Tool and observe that the button click is not a normal chat bubble.

## Level 4: Adaptive Cards

- **Learn:** schema, body/input elements, `Action.Submit`, payloads, validation, card update, activity IDs.
- **Why:** Cards are the project's UI.
- **Project link:** `cards/*.py` and `utils/adaptive_card_loader.py`.
- **Exercise:** Add a required field to the form and verify both card-side and server-side validation.

## Level 5: State Management

- **Learn:** conversation vs user state, storage providers, serialization, lifetime, concurrency, idempotency.
- **Why:** The workflow pauses between activities.
- **Project link:** `WorkflowController._sessions`, `WorkflowState`, `DocumentWorkflowState`.
- **Exercise:** Simulate duplicate review confirmation and verify vendor creation is not repeated.

## Level 6: Workflow Orchestration

- **Learn:** state machines, pause/resume, workflow indexes, step dispatch, decisions, retry logic, compensation.
- **Why:** The config decides next action while state decides whether it is valid now.
- **Project link:** `WorkflowService.current_step()` and cursor advancement.
- **Exercise:** Add a third France document and verify it is requested sequentially.

## Level 7: Software Design Patterns

- **Learn:** Factory, Strategy, State, Builder, Dispatcher, Dependency Injection, Repository, Pipeline.
- **Why:** These patterns keep configuration, UI, state, and operations separated.
- **Project link:** `OperationFactory`, `BaseOperation`, `CardRouter`, card builders, `ProgressService`.
- **Exercise:** Refactor `OperationFactory` in a test to inject fake operations.

## Level 8: Document Processing

- **Learn:** file metadata, MIME types, extension validation, OCR architecture, extraction, external validation, long-running work.
- **Why:** Production onboarding depends on safe file handling.
- **Project link:** `_extract_document_value()`, `submit_document()`, mock OCR/validation services.
- **Exercise:** Add MIME-type metadata validation to document submit tests.

## Level 9: Production Engineering

- **Learn:** structured logging, metrics, tracing, secrets, authentication, authorization, retries, circuit breakers, rate limiting, PII protection.
- **Why:** Vendor onboarding handles sensitive documents and master-data changes.
- **Project link:** `utils/logging.py`, `config.py`, mock services.
- **Exercise:** Add a redaction helper and use it in payload logging tests.

## Level 10: Scaling and Advanced Architecture

- **Learn:** Redis, Celery, Azure Service Bus, background workers, proactive messaging, Cosmos DB, Blob Storage, distributed locks, exactly-once vs at-least-once processing, horizontal scaling.
- **Why:** Long-running document processing should not block bot turns.
- **Project link:** `services/redis_service.py` placeholder and Phase 2 comments in `WorkflowController`.
- **Exercise:** Design a queue message that contains conversation ID, document type, and progress activity ID.
