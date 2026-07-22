# One-to-One Chat Flow

This folder is intended for one-to-one conversational flows, where the bot engages in a direct chat rather than a structured vendor onboarding path.

## Current status

- `chat_flow.py` is present as a placeholder module.
- The flow is not currently implemented in this version of the demo.

## Intended behavior

A one-to-one chat flow can include:

- freeform user interactions
- conversational help or support
- guided question-and-answer sequences
- small talk or contextual prompts before routing into a structured flow

## Suggested design

- Implement a chat controller that handles plain text and conversational payloads.
- Keep it decoupled from the vendor onboarding state machine.
- Optionally route users into `vendor_create`, `vendor_existing`, or `vendor_status` flows based on intent.
