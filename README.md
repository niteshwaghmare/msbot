# Vendor Onboarding Demo Bot

Vendor Onboarding Demo Bot is a Python Microsoft Bot Framework application that demonstrates a configuration-driven vendor onboarding workflow for Microsoft Teams and the Bot Framework Emulator.

## Overview

The bot guides a user through a vendor creation journey:

```text
Select country -> choose operation -> load country workflow -> request one document -> process configured operations -> update progress card -> request next document -> collect vendor information -> review -> confirm -> create vendor
```

The current France `Create` path is the most complete Phase 1 flow: it requests AVIS, processes OCR/validation/SIRET/duplicate-check steps, then requests RIB, processes OCR/bank validation, collects VAT number, email, and phone, shows a review card, and executes `CREATE_VENDOR`.

## Key Capabilities

- Bot Framework `CloudAdapter` endpoint at `POST /api/messages`.
- Teams/Emulator activity handling through `ActivityHandler` and `TurnContext`.
- Adaptive Cards for country selection, operation selection, document upload, progress, vendor information, and review.
- Country-specific JSON configuration in `config_data/countries.json`.
- Sequential document processing for the France document-style workflow.
- Configuration-driven operation resolution through `OperationFactory` and `BaseOperation` implementations.
- In-place progress-card updates using stored activity IDs and `turn_context.update_activity()`.
- In-memory per-conversation workflow sessions.
- Server-side form and upload validation.
- Logging with conversation, channel, user, activity, and activity type context.
- Mock-first operation services for OCR, validation, SIRET, TIN, bank, GST, duplicate check, and vendor creation.

## Technology Stack

- Python 3.10+ syntax, including `dataclasses`, `Enum`, and `async`/`await`.
- `aiohttp` web server.
- Microsoft Bot Framework SDK packages: `botbuilder-core` and `botbuilder-integration-aiohttp`.
- Adaptive Cards JSON generated in Python.
- JSON configuration.
- Python `unittest` tests; tests can also be discovered by `pytest` if installed separately.
- Node.js package `@microsoft/teams-app-test-tool` for local Teams-style testing.

## Project Structure

```text
app.py                         # aiohttp entry point, CloudAdapter, /api/messages route
config.py                      # Bot Framework app id/password/type/tenant and host/port settings
bot/                           # ActivityHandler and composition root
flows/router.py                # Adaptive Card action dispatcher
flows/vendor_create/           # Vendor onboarding workflow controller and state service
config_data/countries.json     # Country, document, operation, and workflow configuration
config_data/country_config.py  # Config loader and structural validator
models/                        # Country, workflow, progress, vendor, and document data models
cards/                         # Adaptive Card builders
core/                          # BaseOperation, OperationFactory, ProcessingContext, generic processor
services/                      # Mock operation services and progress service
utils/                         # Logging and Adaptive Card envelope helpers
tests/                         # Workflow and logging unit tests
```

## Quick Start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
npm install
```

### 3. Configure environment variables

For local Emulator/test-tool use, Bot Framework credentials may remain empty. For a registered bot, provide:

```bash
export MicrosoftAppId="<app-id>"
export MicrosoftAppPassword="<app-password>"
export MicrosoftAppType="MultiTenant"
export MicrosoftAppTenantId="<tenant-id>"
```

Optional runtime settings:

```bash
export HOST=localhost
export PORT=3978
export ENVIRONMENT=local
export LOG_LEVEL=DEBUG
export LOG_FILE=logs/app.log
```

### 4. Run locally

```bash
python3 app.py
```

The endpoint is:

```text
http://localhost:3978/api/messages
```

### 5. Teams App Test Tool

In a separate terminal:

```bash
npx @microsoft/teams-app-test-tool start
```

### 6. Run tests

```bash
python3 -m unittest
```

## Documentation Index

- [01 - Application Overview](docs/01-application-overview.md)
- [02 - Application Flow](docs/02-application-flow.md)
- [03 - Architecture](docs/03-architecture.md)
- [04 - Design Patterns](docs/04-design-patterns.md)
- [05 - Adaptive Cards](docs/05-adaptive-cards.md)
- [06 - Workflow Engine](docs/06-workflow-engine.md)
- [07 - State Management](docs/07-state-management.md)
- [08 - Document Processing](docs/08-document-processing.md)
- [09 - Error Handling and Logging](docs/09-error-handling-and-logging.md)
- [10 - Testing Strategy](docs/10-testing-strategy.md)
- [11 - Extension Guide](docs/11-extension-guide.md)
- [12 - Learning Roadmap](docs/12-learning-roadmap.md)
- [13 - Techniques Explored](docs/13-techniques-explored.md)
- [14 - Production Readiness](docs/14-production-readiness.md)
