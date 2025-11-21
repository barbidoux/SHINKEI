"""Enhanced JWT security utilities."""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
from jose import jwt, JWTError
from jose.exceptions import JWSError
from shinkei.config import settings
from shinkei.exceptions import AuthenticationError
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


def create_access_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with enhanced security claims.

    Args:
        subject: User ID or identifier (sub claim)
        additional_claims: Additional claims to include in the token
        expires_delta: Custom expiration time (defaults to config value)

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token("user-123", {"role": "admin"})
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    claims = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "type": "access",  # Token type
        "jti": str(uuid.uuid4()),  # SECURITY FIX: Unique token identifier for blacklisting
    }

    # Add additional claims if provided
    if additional_claims:
        claims.update(additional_claims)

    # Encode token
    encoded_jwt = jwt.encode(
        claims,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def create_refresh_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        subject: User ID or identifier (sub claim)
        additional_claims: Additional claims to include in the token

    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(
        days=settings.refresh_token_expire_days
    )

    claims = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",  # Explicitly mark as refresh token
        "jti": str(uuid.uuid4()),  # SECURITY FIX: Unique token identifier for blacklisting
    }

    if additional_claims:
        claims.update(additional_claims)

    encoded_jwt = jwt.encode(
        claims,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def decode_token(
    token: str,
    expected_type: str = "access",
    verify_expiration: bool = True
) -> Dict[str, Any]:
    """
    Decode and validate JWT token with enhanced security checks.

    Args:
        token: JWT token to decode
        expected_type: Expected token type ("access" or "refresh")
        verify_expiration: Whether to verify token expiration

    Returns:
        Decoded token payload

    Raises:
        AuthenticationError: If token is invalid, expired, or wrong type

    Example:
        >>> payload = decode_token(token, expected_type="access")
        >>> user_id = payload["sub"]
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": verify_expiration}
        )

        # Verify token type
        token_type = payload.get("type")
        if token_type != expected_type:
            logger.warning(
                "jwt_wrong_type",
                expected=expected_type,
                actual=token_type
            )
            raise AuthenticationError(
                f"Invalid token type. Expected {expected_type}, got {token_type}",
                details={"token_type": token_type}
            )

        # Verify required claims
        if "sub" not in payload:
            raise AuthenticationError(
                "Token missing required 'sub' claim",
                details={"claims": list(payload.keys())}
            )

        # Additional security check: verify issued-at time
        if "iat" in payload:
            issued_at = datetime.fromtimestamp(payload["iat"])
            # Token can't be issued in the future (allow 2 minutes clock skew)
            if issued_at > datetime.utcnow() + timedelta(minutes=2):
                logger.warning("jwt_future_issued_at", iat=issued_at.isoformat())
                raise AuthenticationError("Token has future issued-at time")

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("jwt_expired")
        raise AuthenticationError(
            "Token has expired",
            details={"expired": True}
        )
    except jwt.JWTClaimsError as e:
        logger.warning("jwt_claims_error", error=str(e))
        raise AuthenticationError(
            "Token claims are invalid",
            details={"error": str(e)}
        )
    except JWSError as e:
        logger.warning("jwt_jws_error", error=str(e))
        raise AuthenticationError(
            "Could not validate token signature",
            details={"error": str(e)}
        )
    except JWTError as e:
        logger.warning("jwt_decode_error", error=str(e))
        raise AuthenticationError(
            "Could not validate token",
            details={"error": str(e)}
        )


def verify_token_not_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted (revoked).

    This is a placeholder for token blacklist functionality.
    In production, implement with Redis or database to store revoked tokens.

    Args:
        token: JWT token to check

    Returns:
        True if token is valid (not blacklisted), False if blacklisted

    TODO: Implement actual blacklist storage (Redis recommended)
    """
    # Placeholder - in production, check Redis/DB for blacklisted tokens
    # Example Redis key: f"token:blacklist:{token_jti}"
    return True


def extract_user_id(token: str) -> str:
    """
    Extract user ID from token without full validation.

    Useful for logging and auditing before full authentication.

    Args:
        token: JWT token

    Returns:
        User ID from token, or "unknown" if extraction fails
    """
    try:
        # Decode without verification for auditing purposes only
        payload = jwt.decode(
            token,
            settings.secret_key,  # Still need key for jose
            algorithms=[settings.algorithm],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload.get("sub", "unknown")
    except Exception:
        return "unknown"


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get token expiration time without validation.

    Args:
        token: JWT token

    Returns:
        Expiration datetime, or None if not available
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_signature": False, "verify_exp": False}
        )
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
    except Exception:
        pass

    return None


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired without full validation.

    Args:
        token: JWT token

    Returns:
        True if expired, False otherwise
    """
    expiration = get_token_expiration(token)
    if expiration:
        return datetime.utcnow() > expiration
    return True
