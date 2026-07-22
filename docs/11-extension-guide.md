# 11 - Extension Guide

## Add a New Country

1. Add an entry under `countries` in `config_data/countries.json`.
2. Define `countryCode` and `currency`.
3. Add `documents` with `documentType`, `displayName`, `required`, `minFiles`, `maxFiles`, `allowMultiple`, and `allowedExtensions` where needed.
4. Prefer the France-style top-level `document` stages with nested `steps` because the active conversation flow handles that model.
5. Add `form`, `review`, and final `operation` stages if the country uses the vendor creation flow.
6. Ensure operation names are registered in `OperationFactory._operations`.
7. Run `python3 -m unittest` and add country-specific workflow tests.

## Add a New Document Type

1. Add document metadata under the country `documents` list.
2. Add a top-level `document` workflow step referencing that `documentType`.
3. Add nested `operation` or `decision` steps with unique IDs.
4. Confirm allowed extensions and file-count rules.
5. Add tests for document order, upload validation, and progression to the next step.

## Add a New Operation

1. Create a service class in `services/` that inherits `BaseOperation`.
2. Implement `async def execute(self, context)` and return the updated `ProcessingContext`.
3. Register the instance in `OperationFactory._operations` with the exact operation name used in JSON.
4. Add the operation to `operationRegistry` in `config_data/countries.json` if you want configuration metadata to list it.
5. Reference the operation in a workflow step.
6. Add unit tests for successful execution and failure behavior.

## Add a New Form Field

1. Add the field to a `form` step's `fields` array.
2. Use supported field types validated by `ConfigService`: `text`, `email`, `tel`, `number`, `date`, or `choice`.
3. Update server-side validation in `WorkflowService.submit_form()` if the new field needs custom rules.
4. Update review labeling in `ReviewCard.render()` if a friendly label is needed.
5. Add tests for valid/invalid payloads and review rendering.

## Add a New Workflow Step Type

1. Extend `ConfigService._validate_country()` to validate the new type.
2. Extend `WorkflowService.start_current_workflow_step()` for pause/resume semantics.
3. Extend `WorkflowController._send_current_step()` or processing logic to execute/render it.
4. Add state fields if needed and test duplicate/retry behavior.

## Add a New Adaptive Card

Place the builder in `cards/`, define action constants near the builder, use `build_card()`/`to_attachment()`, and add router/controller handling for any submitted action.

## Add a Real External API

Replace a mock service implementation behind the `BaseOperation` contract. Keep Bot Framework and card rendering out of the service. Add timeouts, retries, redaction, configuration for credentials, and tests with fake clients.
