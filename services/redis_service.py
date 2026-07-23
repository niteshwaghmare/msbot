"""
This module provides a centralized Redis client manager used by the
application to persist and retrieve session data and other cache-backed
state.

The service supports two authentication modes controlled by configuration:

1. password
   Used mainly for local development or Redis instances that use username /
   password or access key based authentication.

2. entra
   Used for Azure Redis environments such as dev, qc, uat, and prod where
   Microsoft Entra authentication is enabled.

The authentication mode is resolved dynamically from configuration:

    REDIS__AUTH_MODE=password
    REDIS__AUTH_MODE=entra

Responsibilities:
    - Initialize the Redis client.
    - Select the correct authentication mechanism based on config.
    - Validate Redis connectivity using ping.
    - Expose common Redis operations such as get, set, and delete.
    - Close the Redis connection during application shutdown.
    - Keep Redis connection logic separate from business/session logic.

This service intentionally does not contain session-specific behavior.
Session orchestration is handled by session_service.py.

Typical usage:
    from services.redis_service import redis_service

    redis_service.connect()

    redis_service.set("key", "value", ttl=3600)
    value = redis_service.get("key")
    redis_service.delete("key")

    redis_service.disconnect()
"""

from __future__ import annotations
import json

import redis
from redis import Redis

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

try:
    from redis_entraid.cred_provider import create_from_default_azure_credential
except ImportError:
    create_from_default_azure_credential = None


class RedisService:

    """
    Manages Redis connection lifecycle and common Redis operations.

    RedisService is responsible for creating a Redis client using the
    configured authentication mode. It supports both password-based Redis
    authentication and Microsoft Entra based authentication.

    The service keeps a single Redis client instance for reuse across the
    application process. Consumers should not create Redis clients directly.
    Instead, they should use this service for all Redis interactions.

    Auth mode behavior:
        - password:
            Creates Redis client using host, port, username, password, and SSL
            configuration.

        - entra:
            Creates Redis client using redis-entraid credential provider and
            DefaultAzureCredential flow.

    Important:
        This service expects configuration to be loaded before connect() is
        called.

    Raises:
        RuntimeError:
            If Redis client is accessed before initialization.
        RuntimeError:
            If Entra auth is configured but required dependency is missing.
        redis.RedisError:
            If Redis connection or operation fails.

    Example:
        redis_service.connect()
        redis_service.set("vendor_onboarding:session:123", payload, ttl=86400)
        session = redis_service.get("vendor_onboarding:session:123")
    """

    def __init__(self) -> None:
        self._client: Redis | None = None

    def connect(self) -> None:
        """
        Initialize Redis connection.
        """
        if self._client:
            return

        logger.info(
            "Connecting to Redis host=%s auth_mode=%s",
            settings.redis.host,
            settings.redis.auth_mode,
        )

        if settings.redis.auth_mode == "entra":
            self._client = self._create_entra_client()
        else:
            self._client = self._create_password_client()

        self._client.ping()

        logger.info("Redis connection established successfully")

    def disconnect(self) -> None:
        """
        Close Redis connection.
        """
        if self._client:
            self._client.close()
            self._client = None

            logger.info("Redis connection closed")

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis is not connected")

        return self._client

    def get(self, key: str):
        return self.client.get(key)

    def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        return self.client.set(
            key,
            value,
            ex=ttl,
        )

    
    def set_json(
        self,
        key: str,
        value: dict,
        ttl: int | None = None,
    ) -> bool:
        return self.set(
            key=key,
            value=json.dumps(value, ensure_ascii=False),
            ttl=ttl,
        )


    def get_json(
        self,
        key: str,
    ) -> dict | None:

        value = self.get(key)

        if not value:
            return None

        return json.loads(value)


    def delete(self, key: str) -> int:
        return self.client.delete(key)

    def _create_password_client(self) -> Redis:
        return redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            username=settings.redis.username,
            password=(
                settings.redis.password.get_secret_value()
                if settings.redis.password
                else None
            ),
            ssl=settings.redis.ssl,
            decode_responses=True,
        )

    def _create_entra_client(self) -> Redis:
        if create_from_default_azure_credential is None:
            raise RuntimeError(
                "redis-entraid package is not installed"
            )

        credential_provider = create_from_default_azure_credential(
            ("https://redis.azure.com/.default",)
        )

        return redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            ssl=settings.redis.ssl,
            credential_provider=credential_provider,
            decode_responses=True,
        )


redis_service = RedisService()