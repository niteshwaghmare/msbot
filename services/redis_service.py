# services/redis_service.py
"""Simple Redis connection manager."""

from __future__ import annotations

import os
import json
import redis
from redis import Redis
from redis.exceptions import AuthenticationError, ConnectionError as RedisConnectionError

from core.logging import get_logger

logger = get_logger(__name__)


class RedisService:
    """Manages Redis connection for session storage."""

    def __init__(self) -> None:
        self._client: Redis | None = None

    def connect(self) -> None:
        """Initialize Redis connection."""
        if self._client:
            return

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = "myredispassword"
        ssl = os.getenv("REDIS_SSL", "false").lower() == "true"

        # Validate configuration
        if not password:
            logger.warning("REDIS_KEY environment variable is not set or empty")
            password = None

        logger.info(
            "Connecting to Redis host=%s password=%s port=%s ssl=%s",
            host,
            password,
            port,
            ssl,
        )

        try:
            self._client = redis.Redis(
                host=host,
                port=port,
                password=password,
                ssl=ssl,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            # Test connection
            self._client.ping()
            logger.info("Redis connection established successfully")

        except AuthenticationError as e:
            self._client = None
            error_msg = f"Redis authentication failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(
                f"Failed to authenticate with Redis. Check REDIS_KEY is correct. Error: {str(e)}"
            ) from e

        except RedisConnectionError as e:
            self._client = None
            error_msg = f"Redis connection failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(
                f"Failed to connect to Redis at {host}:{port}. Ensure Redis is running. Error: {str(e)}"
            ) from e

        except Exception as e:
            self._client = None
            error_msg = f"Unexpected Redis error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(f"Unexpected Redis error: {str(e)}") from e

    def disconnect(self) -> None:
        """Close Redis connection."""
        try:
            if self._client:
                self._client.close()
                self._client = None
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis is not connected. Call connect() first.")
        return self._client

    def get(self, key: str) -> str | None:
        """Get value by key."""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {str(e)}")
            raise

    def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set key-value with optional TTL in seconds."""
        try:
            return self.client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {str(e)}")
            raise

    def delete(self, key: str) -> int:
        """Delete key."""
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {str(e)}")
            raise

    def get_json(self, key: str) -> dict | None:
        """Get JSON value by key."""
        try:
            value = self.get(key)
            if not value:
                return None
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key '{key}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Redis GET_JSON error for key '{key}': {str(e)}")
            raise

    def set_json(self, key: str, value: dict, ttl: int | None = None) -> bool:
        """Set JSON value with optional TTL in seconds."""
        try:
            return self.set(key, json.dumps(value, ensure_ascii=False), ttl=ttl)
        except json.JSONEncodeError as e:
            logger.error(f"JSON encode error for key '{key}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Redis SET_JSON error for key '{key}': {str(e)}")
            raise


# Global singleton instance
redis_service = RedisService()