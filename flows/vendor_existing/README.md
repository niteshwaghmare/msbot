# Vendor Existing Flow

This folder is intended for the vendor existing flow: interactions involving vendors that already exist in the system.

## Current status

- `existing_flow.py` is present as a placeholder module.
- The flow is not currently implemented in this version of the demo.

## Intended behavior

A vendor existing flow typically handles scenarios such as:

- looking up an existing vendor record
- updating vendor details or documents
- approving or rejecting vendor changes
- returning the user to a relevant next step

## Suggested design

- Implement a dedicated controller for the existing vendor path.
- Keep the flow logic separate from the `vendor_create` onboarding flow.
- Reuse shared card builders where possible, but use flow-specific cards for lookup and update.
