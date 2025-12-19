"""Token Blacklist Port - Interface for JWT blacklist operations."""

from abc import ABC, abstractmethod


class TokenBlacklistPort(ABC):
    """Port for JWT token blacklist operations.

    Defines the interface for blacklisting and checking JWT tokens.
    Used to invalidate tokens before their natural expiration (e.g., on logout).
    """

    @abstractmethod
    def add_to_blacklist(self, jti: str, ttl_seconds: int) -> None:
        """Add a token ID to the blacklist.

        Args:
            jti: The JWT ID (jti claim) to blacklist.
            ttl_seconds: Time-to-live in seconds (should match token expiry).
        """
        pass

    @abstractmethod
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token ID is blacklisted.

        Args:
            jti: The JWT ID (jti claim) to check.

        Returns:
            True if the token is blacklisted, False otherwise.
        """
        pass

    @abstractmethod
    def remove_from_blacklist(self, jti: str) -> None:
        """Remove a token ID from the blacklist.

        Args:
            jti: The JWT ID (jti claim) to remove.
        """
        pass
