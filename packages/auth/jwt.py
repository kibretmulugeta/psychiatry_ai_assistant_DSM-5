"""
JWT Token utility module for access token creation, verification, and decoding.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from apps.backend.app.core.config import settings
from packages.shared.exceptions import BaseAppException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationException(BaseAppException):
    """Raised when authentication or token validation fails."""

    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401,
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create signed JWT access token.

    Args:
        subject: Unique identifier for the token subject (e.g. user_id or session_id).
        expires_delta: Optional custom duration. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES setting.
        additional_claims: Extra claims payload.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": "access_token",
    }
    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: Signed JWT string.

    Returns:
        Decoded payload claims dictionary.

    Raises:
        AuthenticationException if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise AuthenticationException(message=f"Could not validate token: {str(e)}")
