"""Security utilities for input sanitization, validation, and authentication."""
from shinkei.security.sanitizers import (
    sanitize_html,
    sanitize_json,
    validate_url,
    check_max_length
)
from shinkei.security.validators import (
    SanitizedStr,
    SafeURL,
    LimitedStr
)
from shinkei.security.password import (
    validate_password_strength,
    validate_password_or_raise,
    check_password_common_patterns,
    estimate_password_entropy
)
from shinkei.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_not_blacklisted,
    extract_user_id,
    get_token_expiration,
    is_token_expired
)

__all__ = [
    # Sanitizers
    "sanitize_html",
    "sanitize_json",
    "validate_url",
    "check_max_length",
    # Validators
    "SanitizedStr",
    "SafeURL",
    "LimitedStr",
    # Password security
    "validate_password_strength",
    "validate_password_or_raise",
    "check_password_common_patterns",
    "estimate_password_entropy",
    # JWT utilities
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token_not_blacklisted",
    "extract_user_id",
    "get_token_expiration",
    "is_token_expired",
]
