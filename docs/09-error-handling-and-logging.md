# 09 - Error Handling and Logging

## Existing Logging

`app.py` calls `configure_logging()` at startup. Logs include timestamp, level, logger name, conversation ID, channel ID, user ID, user name, activity ID, activity type, and message. The default log level is `DEBUG`; `LOG_LEVEL` can override it. Logs go to stderr and to `logs/app.log` unless `LOG_FILE` is set.

Logged events include:

- Received activities in `app.py`.
- Message routing details in `DemoActivityHandler`.
- Card action and payload keys in `CardRouter`.
- Session creation, country selection, and operation selection in `WorkflowController`.
- Workflow and operation progress in `core.DocumentProcessor`.
- Individual mock operation execution in service classes.
- Adapter-level unhandled exceptions in `on_error()`.

## Existing Error Handling

- Adapter-level `on_error()` logs the exception and sends `The bot hit an error. Please try again.`
- Invalid document phase, missing upload value, and `WorkflowError` during document submit produce safe user messages.
- Document operation exceptions are caught in `_process_current_document()`, mark the document/workflow failed, update progress, and notify the user.
- Unknown operation names raise `ValueError` in `OperationFactory.get()`.
- Configuration file errors raise `ConfigError` during startup/config construction.

## Sensitive Data Not to Log

Do not log document contents, attachment content URLs with secrets, authentication tokens, full VAT/tax IDs, full phone numbers, email addresses, OCR text, bank account numbers, or raw Adaptive Card payloads containing PII.

## Error Categories to Track

| Category | Current handling |
| --- | --- |
| Invalid Adaptive Card payload | Some missing/unknown actions restart the flow; some payload fields may raise. |
| Missing action | Route to country card. |
| Unknown workflow step | `WorkflowError` or `ValueError`. |
| Unsupported operation | `ValueError` from factory. |
| Invalid document type/upload | `WorkflowError` shown to user. |
| Operation failure | Document/workflow failed with safe message. |
| Card update failure | Not specifically caught; adapter-level handler catches unhandled failures. |
| Deleted/expired message | Not specifically handled. |
| State persistence failure | Not applicable to in-memory state. |
| Duplicate submission | Partially handled by workflow flags and completed step checks. |
| Configuration error | Raises at config load. |

## Recommendations

Add structured event names, correlation IDs, duration logging in the active controller loop, specific handling for `update_activity()` failures, redaction helpers, retry policy for transient external calls, and user-facing Adaptive Card error states. Avoid broad silent exception handling because it hides data corruption and duplicate vendor creation risks.
