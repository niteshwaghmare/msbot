# Vendor Onboarding Demo Bot

This project is a Microsoft Teams bot built with the Bot Framework that demonstrates a vendor onboarding workflow. It guides the user through selecting a country, choosing an operation, collecting required documents, and simulating processing.

## Features

- Country selection card
- Operation selection card
- Step-by-step document collection
- Local mode: asks for a file path
- Deployed/Teams mode: expects document attachments
- Simulated processing progress updates

## Prerequisites

- Python 3.10+
- Node.js and npm
- Microsoft Teams environment or the Teams App Test Tool

## Setup

1. Change into the project folder:
   ```bash
   cd DemoBot
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Node dependencies:
   ```bash
   npm install
   ```

## Start the bot

Run these commands in separate terminals:

Terminal 1:
```bash
npx @microsoft/teams-app-test-tool start
```

Terminal 2:
```bash
python3 app.py
```

The bot endpoint will be available at:
```text
http://localhost:3978/api/messages
```

## Project structure

- app.py: aiohttp entry point, bot adapter setup, and routes
- config.py: app settings for adapter credentials, host, and port
- bot/: Bot ActivityHandler and composition root
- flows/: Conversation routing and vendor operation flows
- config_data/: JSON-backed country/document configuration provider
- models/: Vendor, document, country, workflow, and progress models
- cards/: Adaptive Card builders and templates
- services/: External-service integration layer placeholders plus progress service
- validators/: Validation extension points
- processors/: Document and vendor processing pipeline modules
- state/: Conversation and vendor state extension points
- utils/: Shared helpers
- tests/: Workflow unit tests

## Notes

- For local testing, the bot prompts for a file path.
- In deployed/Teams usage, upload the document as an attachment when prompted.
