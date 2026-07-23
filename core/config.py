"""Core application settings shared by infrastructure services."""

from __future__ import annotations

import os
from dataclasses import dataclass


class SecretValue:
    """Small compatibility wrapper exposing ``get_secret_value``."""

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


@dataclass(frozen=True)
class RedisSettings:
    host: str = os.getenv("REDIS__HOST", os.getenv("REDIS_HOST", "localhost"))
    port: int = int(os.getenv("REDIS__PORT", os.getenv("REDIS_PORT", "6379")))
    username: str | None = (
        os.getenv("REDIS__USERNAME", os.getenv("REDIS_USERNAME")) or None
    )
    password: SecretValue | None = (
        SecretValue(os.getenv("REDIS__PASSWORD", os.getenv("REDIS_PASSWORD", "")))
        if os.getenv("REDIS__PASSWORD", os.getenv("REDIS_PASSWORD"))
        else None
    )
    ssl: bool = os.getenv("REDIS__SSL", os.getenv("REDIS_SSL", "false")).lower() in {
        "1",
        "true",
        "yes",
    }
    auth_mode: str = os.getenv(
        "REDIS__AUTH_MODE",
        os.getenv("REDIS_AUTH_MODE", "password"),
    ).lower()


@dataclass(frozen=True)
class SessionSettings:
    ttl_seconds: int = int(
        os.getenv("SESSION__TTL_SECONDS", os.getenv("SESSION_TTL_SECONDS", "86400"))
    )
    key_prefix: str = os.getenv(
        "SESSION__KEY_PREFIX",
        os.getenv("SESSION_KEY_PREFIX", "vendor_onboarding:session:"),
    )


@dataclass(frozen=True)
class Settings:
    redis: RedisSettings = RedisSettings()
    session: SessionSettings = SessionSettings()


settings = Settings()
