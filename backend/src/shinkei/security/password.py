"""Password validation and security utilities."""
import re
from typing import Tuple
from shinkei.config import settings
from shinkei.exceptions import ValidationError


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.

    Checks:
    - Minimum length (from config)
    - Complexity requirements (if enabled in config):
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message will be empty string.

    Example:
        >>> is_valid, msg = validate_password_strength("Test123!")
        >>> if not is_valid:
        ...     raise ValidationError(msg)
    """
    if len(password) < settings.password_min_length:
        return (
            False,
            f"Password must be at least {settings.password_min_length} characters long"
        )

    if settings.require_password_complexity:
        checks = {
            "uppercase": (r"[A-Z]", "at least one uppercase letter"),
            "lowercase": (r"[a-z]", "at least one lowercase letter"),
            "digit": (r"\d", "at least one number"),
            "special": (r'[!@#$%^&*(),.?":{}|<>]', "at least one special character"),
        }

        missing = []
        for check_name, (pattern, description) in checks.items():
            if not re.search(pattern, password):
                missing.append(description)

        if missing:
            return (
                False,
                f"Password must contain {', '.join(missing)}"
            )

    return (True, "")


def validate_password_or_raise(password: str) -> None:
    """
    Validate password and raise ValidationError if invalid.

    Args:
        password: Password to validate

    Raises:
        ValidationError: If password doesn't meet requirements
    """
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        raise ValidationError(
            error_message,
            field="password",
            details={
                "min_length": settings.password_min_length,
                "complexity_required": settings.require_password_complexity
            }
        )


def check_password_common_patterns(password: str) -> bool:
    """
    Check if password contains common weak patterns.

    Checks for:
    - Sequential characters (abc, 123)
    - Repeated characters (aaa, 111)
    - Common words (password, admin, etc.)

    Args:
        password: Password to check

    Returns:
        True if password contains weak patterns, False otherwise
    """
    # Convert to lowercase for checking
    lower_pass = password.lower()

    # Common weak passwords
    weak_passwords = {
        "password", "admin", "user", "root", "test", "guest",
        "123456", "qwerty", "abc123", "letmein", "welcome"
    }

    # Check for common weak passwords
    if lower_pass in weak_passwords:
        return True

    # Check for sequential numbers
    if re.search(r"(012|123|234|345|456|567|678|789)", password):
        return True

    # Check for sequential letters
    if re.search(r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)", lower_pass):
        return True

    # Check for 3+ repeated characters
    if re.search(r"(.)\1{2,}", password):
        return True

    return False


def estimate_password_entropy(password: str) -> float:
    """
    Estimate password entropy (randomness).

    Higher entropy = stronger password.
    Typical ranges:
    - < 28 bits: Very weak
    - 28-35 bits: Weak
    - 36-59 bits: Reasonable
    - 60-127 bits: Strong
    - >= 128 bits: Very strong

    Args:
        password: Password to analyze

    Returns:
        Estimated entropy in bits
    """
    import math

    # Calculate character set size
    charset_size = 0

    has_lowercase = bool(re.search(r"[a-z]", password))
    has_uppercase = bool(re.search(r"[A-Z]", password))
    has_digits = bool(re.search(r"\d", password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;/]', password))

    if has_lowercase:
        charset_size += 26
    if has_uppercase:
        charset_size += 26
    if has_digits:
        charset_size += 10
    if has_special:
        charset_size += 32  # Common special characters

    if charset_size == 0:
        return 0.0

    # Entropy = log2(charset_size^length)
    entropy = len(password) * math.log2(charset_size)

    return round(entropy, 2)
