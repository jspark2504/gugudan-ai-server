"""Token Blacklist Repository implementation using Redis."""

from typing import Optional

import redis

from app.auth.application.port.token_blacklist_port import TokenBlacklistPort
from config.redis_config import get_redis


class TokenBlacklistImpl(TokenBlacklistPort):
    """Redis implementation of TokenBlacklistPort.

    Blacklisted tokens are stored in Redis with TTL-based expiration.
    Key format: blacklist:{jti}
    Value: "1" (simple marker)

    The TTL should match the token's remaining validity period,
    so entries auto-expire when the token would have expired anyway.
    """

    KEY_PREFIX = "blacklist:"

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize with Redis client.

        Args:
            redis_client: Redis client instance. Uses default if not provided.
        """
        self._redis = redis_client or get_redis()

    def _make_key(self, jti: str) -> str:
        """Create Redis key for blacklisted token."""
        return f"{self.KEY_PREFIX}{jti}"

    def add_to_blacklist(self, jti: str, ttl_seconds: int) -> None:
        """Add a token ID to the blacklist.

        Args:
            jti: The JWT ID (jti claim) to blacklist.
            ttl_seconds: Time-to-live in seconds (should match token expiry).
        """
        key = self._make_key(jti)
        self._redis.setex(key, ttl_seconds, "1")

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token ID is blacklisted.

        Args:
            jti: The JWT ID (jti claim) to check.

        Returns:
            True if the token is blacklisted, False otherwise.
        """
        key = self._make_key(jti)
        return self._redis.exists(key) > 0

    def remove_from_blacklist(self, jti: str) -> None:
        """Remove a token ID from the blacklist.

        Args:
            jti: The JWT ID (jti claim) to remove.
        """
        key = self._make_key(jti)
        self._redis.delete(key)
