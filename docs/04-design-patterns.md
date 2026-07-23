# 04 - Design Patterns

## Factory Method / Registry

- **Where:** `core/operation_factory.py`, class `OperationFactory`.
- **Problem:** Workflow config names operations by string (`OCR`, `BANK`, `CREATE_VENDOR`). The runtime needs service objects without a large conditional block.
- **Implementation:** `_operations` maps operation names to `BaseOperation` instances; `get()` returns the selected implementation or raises `ValueError`.
- **Benefit:** Adding an operation requires registering one mapping and then referencing it in JSON.
- **Trade-off:** The registry is static; dependency injection for real clients is not yet implemented.

## Strategy + Abstract Base Class

- **Where:** `core/base_operations.py` and services such as `OCRService`, `ValidationService`, `SIRETService`, `BankService`, `DuplicateCheckService`, `VendorService`.
- **Problem:** OCR, validation, duplicate check, and vendor creation are different algorithms selected at runtime.
- **Implementation:** `BaseOperation.execute(context)` defines a common asynchronous contract. Each concrete service mutates and returns `ProcessingContext`.
- **Benefit:** `WorkflowController` and `DocumentProcessor` can run any operation polymorphically.
- **Trade-off:** The current context is broad and mutable; strong domain result types may be useful later.

## State Machine

- **Where:** `models/workflow.py` and `flows/vendor_create/document_collector.py`.
- **States:** `START`, `COUNTRY_SELECTED`, `OPERATION_SELECTED`, `AWAITING_DOCUMENT`, `PROCESSING`, `AWAITING_FORM`, `AWAITING_REVIEW`, `CREATING_VENDOR`, `COMPLETED`, `FAILED`.
- **Document statuses:** `PENDING`, `WAITING_FOR_UPLOAD`, `UPLOADED`, `PROCESSING`, `COMPLETED`, `FAILED`.
- **Problem:** A Teams conversation pauses after every user input and resumes later.
- **Implementation:** `WorkflowService` transitions state in methods such as `select_country()`, `submit_document()`, `complete_document()`, `submit_form()`, `confirm_review()`, and `edit_form()`.
- **Benefit:** Invalid transitions are rejected and duplicate confirmation/vendor creation is guarded.

## Dispatcher / Router

- **Where:** `flows/router.py`, class `CardRouter`.
- **Problem:** Adaptive Card submits arrive as generic message activities.
- **Implementation:** The router reads payload `action` values (`select_country`, `select_operation`, `submit_documents`, `submit_vendor_information`, `confirm_vendor`, `edit_vendor_information`) and calls controller methods.
- **Benefit:** Routing is centralized and card titles are not parsed.
- **Trade-off:** Unknown actions restart at the country card, which is friendly but can mask stale-card diagnostics.

## Builder Pattern

- **Where:** `cards/country_select_card.py`, `cards/operation_card.py`, `cards/document_upload_card.py`, `cards/details_form_card.py`, `cards/review_card.py`, `cards/progress_card.py`.
- **Problem:** Adaptive Card JSON must be generated consistently.
- **Implementation:** Static `render()` methods build card-specific bodies/actions and `utils.adaptive_card_loader.build_card()` adds schema/type/version.
- **Benefit:** Cards are reusable and all use Adaptive Card version `1.4`.

## Configuration-Driven Design

- **Where:** `config_data/countries.json`, loaded by `ConfigService`.
- **Problem:** Countries require different documents and operation sequences.
- **Implementation:** `documents` define upload metadata; `workflow` defines ordered conversation and processing stages.
- **Hardcoded alternative:** Python branches for France AVIS, France RIB, India GST, etc.
- **Current approach:** Add or change workflow JSON and reuse the same state/orchestration engine.
- **Trade-off:** Configuration validation must stay strong because errors move from code to data.

## Pipeline / Sequential Processing

- **Where:** `WorkflowController._process_current_document()` and `core.DocumentProcessor.run()`.
- **Problem:** A document must be processed through ordered steps with progress after each step.
- **Implementation:** The controller loops through nested configured steps, resolves an operation, executes it, records results, and updates progress.
- **Benefit:** AVIS can complete before RIB is requested, preserving a guided user experience.
