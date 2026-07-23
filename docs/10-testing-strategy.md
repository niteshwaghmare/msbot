# 10 - Testing Strategy

## Existing Tests

The repository currently uses Python `unittest` tests:

- `tests/test_workflow_service.py` verifies France document sequencing, transition from AVIS to RIB, form validation, review/vendor idempotency, document-submit preconditions, and `ConfigError` type coverage.
- `tests/test_logging.py` verifies file logging and selected third-party logger levels.

Run them with:

```bash
python3 -m unittest
```

## Recommended Test Layers

### Unit Tests

- `OperationFactory.get()` returns correct service and rejects unknown operations.
- `ConfigService` validates missing countries, duplicate IDs, invalid documents, unknown field types, and invalid file counts.
- `WorkflowService` state transitions for all phases.
- `DetailsFormCard`, `ReviewCard`, `ProgressCard`, and upload/country/operation cards generate expected actions and inputs.
- Server-side form validation for required, email, min/max length.

### Workflow Tests

- France country selection and operation selection.
- AVIS upload and processing.
- RIB upload and processing.
- Vendor-information form validation and submission.
- Review confirm path.
- Edit path returning to form without rerunning documents.
- Operation failure path marking document and workflow failed.

### Adaptive Card Tests

- Action payload names match router constants.
- Card version is `1.4`.
- Required inputs and error messages are rendered.
- Progress status icons map to `StepStatus` values.

### Idempotency Tests

- Repeated submit for a completed nested operation is not rerun.
- Repeated upload does not add duplicate files when multiple uploads are disallowed.
- Repeated confirm does not create a second vendor.

### Integration Tests

- Simulate Bot Framework message activities and card-submit activities.
- Verify state survives across turns in the same controller instance.
- Verify `update_activity()` is called with the stored progress activity ID.
- Mock external APIs behind `BaseOperation` implementations.

## Mocking External APIs

Keep external clients behind service classes implementing `BaseOperation`. Unit tests should inject fake operations or monkey-patch/register test operations rather than calling real OCR, tax, bank, or vendor-master APIs.
