# Flows

This directory contains the conversation flow implementations for the Vendor Onboarding demo bot. Each subfolder is a self-contained flow or a group of related interactions.

## Structure

- `router.py`
  - Dispatches Adaptive Card submit payload actions to the appropriate flow controller.
  - Routes country selection, operation selection, and document submission into the main flow.

- `vendor_create/`
  - Implements the vendor creation workflow: country selection, operation selection, document collection, and processing.
  - Contains the workflow state-machine and the controller that drives the user through a sequence of cards.

- `vendor_existing/`
  - Intended for handling flows related to existing vendors.
  - Contains scaffolding for a separate conversation path.

- `vendor_status/`
  - Intended for tracking vendor status flows.
  - Contains scaffolding for messages or cards that show ongoing or completed status.

- `one2one/`
  - Intended for direct one-to-one conversational flows.
  - Contains placeholder chat flow logic.

## Notes

- `vendor_create` is the currently implemented flow in this project.
- The other subflows are present as placeholders for future work and may not yet be wired into the bot.
