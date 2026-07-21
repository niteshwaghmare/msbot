"""Application settings for the Vendor Onboarding bot."""

from __future__ import annotations

import os


class BotConfig:
    """Runtime configuration for the Bot Framework adapter."""

    APP_ID: str = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD: str = os.environ.get("MicrosoftAppPassword", "")
    APP_TYPE: str = os.environ.get("MicrosoftAppType", "MultiTenant")
    APP_TENANT_ID: str = os.environ.get("MicrosoftAppTenantId", "")


DEFAULT_HOST: str = os.environ.get("HOST", "localhost")
DEFAULT_PORT: int = int(os.environ.get("PORT", "3978"))
