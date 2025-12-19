"""JWT Token Service Implementation.

Implements JWT token creation and validation with:
- 12-hour expiration
- AES-encrypted user-specific keys
- CSRF token integration
- Token blacklisting support
- Environment-aware secure cookie settings
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.auth.application.port.jwt_token_port import (
    JWTTokenPort,
    TokenPair,
    TokenPayload,
)
from app.auth.application.port.token_blacklist_port import TokenBlacklistPort
from app.common.infrastructure.encryption import TokenKeyGenerator
from config.settings import settings


class JWTTokenService(JWTTokenPort):
    """JWT Token Service.

    Creates and validates JWT tokens with:
    - HS256 algorithm
    - 12-hour validity period
    - AES-encrypted user-specific subject identifier
    - Embedded CSRF token for double-submit cookie pattern
    - Token blacklist support for logout/revocation
    """

    ALGORITHM = "HS256"
    TOKEN_EXPIRY_HOURS = 12

    def __init__(self, blacklist: Optional[TokenBlacklistPort] = None):
        """Initialize JWT token service.

        Args:
            blacklist: Optional token blacklist for revocation support.
        """
        self._secret_key = settings.JWT_SECRET_KEY
        self._master_key = TokenKeyGenerator.derive_key_from_secret(
            settings.JWT_ENCRYPTION_KEY
        )
        self._key_generator = TokenKeyGenerator(self._master_key)
        self._blacklist = blacklist

    def create_token(
        self,
        account_id: int,
        provider: str,
    ) -> TokenPair:
        """Create a new JWT token pair.

        Args:
            account_id: The user's account ID.
            provider: The SSO provider used for authentication.

        Returns:
            TokenPair containing access token and CSRF token.
        """
        # Generate unique JWT ID for blacklisting
        jti = secrets.token_urlsafe(16)

        # Generate CSRF token
        csrf_token = secrets.token_urlsafe(32)

        # Generate encrypted user-specific key
        encrypted_key, encrypted_key_iv = self._key_generator.generate_encrypted_user_key(
            account_id
        )

        # Calculate expiration
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.TOKEN_EXPIRY_HOURS)

        # Create JWT payload
        payload = {
            "jti": jti,
            "sub": str(account_id),
            "enc_key": encrypted_key,
            "enc_iv": encrypted_key_iv,
            "csrf": csrf_token,
            "provider": provider,
            "iat": now,
            "exp": expires_at,
        }

        # Encode JWT
        access_token = jwt.encode(
            payload,
            self._secret_key,
            algorithm=self.ALGORITHM,
        )

        return TokenPair(
            access_token=access_token,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )

    def validate_token(self, token: str) -> Optional[TokenPayload]:
        """Validate a JWT token and extract payload.

        Checks:
        1. Token signature and expiration
        2. Token not in blacklist (if blacklist is configured)

        Args:
            token: The JWT token string.

        Returns:
            TokenPayload if valid, None if invalid, expired, or blacklisted.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self.ALGORITHM],
            )

            jti = payload["jti"]

            # Check if token is blacklisted
            if self._blacklist and self._blacklist.is_blacklisted(jti):
                return None

            return TokenPayload(
                jti=jti,
                account_id=int(payload["sub"]),
                encrypted_key=payload["enc_key"],
                encrypted_key_iv=payload["enc_iv"],
                csrf_token=payload["csrf"],
                provider=payload["provider"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except (KeyError, ValueError):
            return None

    def blacklist_token(self, token: str) -> bool:
        """Add a token to the blacklist.

        Args:
            token: The JWT token string to blacklist.

        Returns:
            True if successfully blacklisted, False otherwise.
        """
        if not self._blacklist:
            return False

        try:
            # Decode without full validation to get jti and exp
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self.ALGORITHM],
                options={"verify_exp": False},  # Allow expired tokens to be blacklisted
            )

            jti = payload["jti"]
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            now = datetime.now(timezone.utc)

            # Calculate remaining TTL (or minimum 1 second)
            ttl_seconds = max(int((exp - now).total_seconds()), 1)

            self._blacklist.add_to_blacklist(jti, ttl_seconds)
            return True
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return False

    def validate_csrf(self, token: str, csrf_token: str) -> bool:
        """Validate that the CSRF token matches the one in the JWT.

        Args:
            token: The JWT token string.
            csrf_token: The CSRF token to validate.

        Returns:
            True if CSRF tokens match, False otherwise.
        """
        payload = self.validate_token(token)
        if payload is None:
            return False
        return secrets.compare_digest(payload.csrf_token, csrf_token)

    def refresh_token(self, token: str) -> Optional[TokenPair]:
        """Refresh an existing token if still valid.

        Args:
            token: The existing JWT token.

        Returns:
            New TokenPair if refresh successful, None otherwise.
        """
        payload = self.validate_token(token)
        if payload is None:
            return None

        # Create new token with same account_id and provider
        return self.create_token(
            account_id=payload.account_id,
            provider=payload.provider,
        )

    def decode_without_verification(self, token: str) -> Optional[dict]:
        """Decode JWT without verification (for debugging/logging).

        WARNING: Do not use for authentication!

        Args:
            token: The JWT token string.

        Returns:
            Decoded payload dict or None.
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False},
            )
        except jwt.InvalidTokenError:
            return None
