# 05 - Adaptive Cards

## Card Infrastructure

All cards use `utils.adaptive_card_loader.build_card()`, which sets schema `http://adaptivecards.io/schemas/adaptive-card.json`, type `AdaptiveCard`, and version `1.4`, then converts the dictionary to a Bot Framework attachment with `CardFactory.adaptive_card()`.

## Implemented Cards

| Card | Builder | Submit action | Sent or updated | Purpose |
| --- | --- | --- | --- | --- |
| Country selection | `CountryCard` | `select_country` | Sent | Choose a configured country from `Input.ChoiceSet`. |
| Operation selection | `OperationCard` | `select_operation` | Sent | Choose configured operation label. |
| Document upload | `UploadCard` | `submit_documents` | Sent | Request one current document; local mode includes `document_path`. |
| Progress | `ProgressCard` | None | Sent once, then updated | Show nested operation status. |
| Vendor information | `DetailsFormCard` | `submit_vendor_information` | Sent | Collect configured form fields. |
| Review | `ReviewCard` | `confirm_vendor`, `edit_vendor_information` | Sent | Review country, document statuses, and form data. |

Current limitation: placeholder modules exist for edit/menu cards, and there is no dedicated duplicate-result, completion, or error-card builder in the active flow. Duplicate check currently records `duplicate_found: False` in mock service and does not render `SHOW_DUPLICATE_CARD`.

## How Action.Submit Reaches the Bot

Adaptive Card submit buttons place their `data` and input values into `turn_context.activity.value`. `DemoActivityHandler.on_message_activity()` reads that value and passes it to `CardRouter.route()`. The router dispatches by payload `action`.

Example country payload:

```json
{
  "action": "select_country",
  "country": "France"
}
```

Example document payload in local mode:

```json
{
  "action": "submit_documents",
  "document": "AVIS",
  "document_path": "/tmp/avis.pdf"
}
```

Example form payload:

```json
{
  "action": "submit_vendor_information",
  "workflowStepId": "vendor_information",
  "vatNumber": "FR12",
  "email": "a@example.com",
  "phone": "1234567"
}
```

## User Selection Visibility

Adaptive Card button clicks usually do not appear as normal user chat bubbles. This project explicitly acknowledges selected values by sending text messages such as `Country selected: France` and `Operation selected: Create`.

## Activity ID and update_activity()

The progress card is sent once. Its returned activity ID is stored in `DocumentWorkflowState.progress_activity_id`. Later updates recreate the card attachment, set `activity.id` to the stored ID, and call `turn_context.update_activity(activity)`. This avoids flooding the chat with one card per operation.

## Validation

Card-side properties such as `isRequired` improve the client experience but are not trusted. `WorkflowService.submit_form()` performs server-side required, email, min length, and max length checks. Upload validation checks active phase, document type, extensions, file counts, and duplicate non-multiple submissions.

## Compatibility

The card schema version is `1.4`. Teams and Emulator support can vary by client/channel, so newly added card features should be tested in the target Teams client, not only by JSON inspection.
