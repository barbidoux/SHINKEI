"""Input sanitization utilities to prevent XSS and injection attacks."""
import bleach
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from shinkei.exceptions import ValidationError
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

# Allowed HTML tags and attributes for user content
# Very restrictive - only basic formatting, no scripts or dangerous elements
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'span', 'div'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'span': ['class'],
    'div': ['class']
}

# Allowed URL schemes
ALLOWED_SCHEMES = ['http', 'https']


def sanitize_html(
    content: str,
    strip: bool = True,
    allowed_tags: Optional[list] = None,
    allowed_attributes: Optional[Dict[str, list]] = None
) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Uses bleach library to remove dangerous HTML elements while
    preserving safe formatting.

    Args:
        content: Raw HTML content to sanitize
        strip: If True, strip disallowed tags. If False, escape them.
        allowed_tags: Custom list of allowed HTML tags (uses ALLOWED_TAGS if None)
        allowed_attributes: Custom dict of allowed attributes (uses ALLOWED_ATTRIBUTES if None)

    Returns:
        Sanitized HTML content safe for storage and display

    Example:
        >>> sanitize_html('<script>alert("xss")</script><p>Safe text</p>')
        '<p>Safe text</p>'
    """
    if not content:
        return content

    tags = allowed_tags or ALLOWED_TAGS
    attrs = allowed_attributes or ALLOWED_ATTRIBUTES

    try:
        # Clean HTML using bleach
        sanitized = bleach.clean(
            content,
            tags=tags,
            attributes=attrs,
            strip=strip,
            protocols=ALLOWED_SCHEMES
        )

        # Additional protection: linkify URLs (converts bare URLs to links safely)
        # This prevents URL-based XSS
        sanitized = bleach.linkify(
            sanitized,
            skip_tags=['pre', 'code']  # Don't linkify in code blocks
        )

        return sanitized

    except Exception as e:
        logger.error("html_sanitization_failed", error=str(e), content_length=len(content))
        # On error, strip ALL HTML as safety measure
        return bleach.clean(content, tags=[], strip=True)


def sanitize_plaintext(content: str) -> str:
    """
    Strip ALL HTML tags from content, returning only plain text.

    Use this for fields that should never contain HTML (titles, names, etc.)

    Args:
        content: Content that may contain HTML

    Returns:
        Plain text with all HTML removed

    Example:
        >>> sanitize_plaintext('<b>Title</b>')
        'Title'
    """
    if not content:
        return content

    try:
        return bleach.clean(content, tags=[], strip=True)
    except Exception as e:
        logger.error("plaintext_sanitization_failed", error=str(e))
        return content


def sanitize_json(data: Any, max_depth: int = 10, current_depth: int = 0) -> Any:
    """
    Recursively sanitize JSON data structures.

    Sanitizes all string values in nested dictionaries and lists
    to prevent stored XSS in JSON fields.

    Args:
        data: JSON-serializable data (dict, list, str, int, etc.)
        max_depth: Maximum nesting depth to prevent DoS
        current_depth: Current recursion depth (internal use)

    Returns:
        Sanitized data structure

    Raises:
        ValidationError: If max depth exceeded

    Example:
        >>> sanitize_json({"key": "<script>xss</script>"})
        {"key": ""}
    """
    if current_depth > max_depth:
        raise ValidationError(
            f"JSON nesting depth exceeds maximum ({max_depth})",
            field="json_data",
            details={"max_depth": max_depth}
        )

    if isinstance(data, dict):
        return {
            sanitize_plaintext(str(k)): sanitize_json(v, max_depth, current_depth + 1)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_json(item, max_depth, current_depth + 1) for item in data]
    elif isinstance(data, str):
        return sanitize_plaintext(data)
    else:
        # int, float, bool, None - safe as-is
        return data


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> str:
    """
    Validate and sanitize URL.

    Ensures URL uses allowed schemes (http/https by default)
    and has valid structure.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid or uses disallowed scheme

    Example:
        >>> validate_url('https://example.com')
        'https://example.com'
        >>> validate_url('javascript:alert(1)')
        # Raises ValidationError
    """
    if not url:
        return url

    schemes = allowed_schemes or ALLOWED_SCHEMES

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme and parsed.scheme not in schemes:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' not allowed",
                field="url",
                details={"allowed_schemes": schemes, "provided_scheme": parsed.scheme}
            )

        # Require scheme and netloc for absolute URLs
        if parsed.scheme and not parsed.netloc:
            raise ValidationError(
                "Invalid URL format: missing domain",
                field="url"
            )

        return url

    except ValueError as e:
        raise ValidationError(
            f"Invalid URL format: {str(e)}",
            field="url"
        )


def check_max_length(
    content: str,
    max_length: int,
    field_name: str = "content"
) -> str:
    """
    Validate content length to prevent DoS attacks.

    Args:
        content: Content to check
        max_length: Maximum allowed length
        field_name: Name of the field (for error messages)

    Returns:
        Content if valid

    Raises:
        ValidationError: If content exceeds max length

    Example:
        >>> check_max_length("short", 100, "title")
        "short"
        >>> check_max_length("x" * 1001, 1000, "title")
        # Raises ValidationError
    """
    if not content:
        return content

    if len(content) > max_length:
        raise ValidationError(
            f"{field_name} exceeds maximum length of {max_length} characters",
            field=field_name,
            details={
                "max_length": max_length,
                "actual_length": len(content),
                "exceeded_by": len(content) - max_length
            }
        )

    return content


def sanitize_and_validate(
    content: str,
    allow_html: bool = False,
    max_length: Optional[int] = None,
    field_name: str = "content"
) -> str:
    """
    Combined sanitization and validation for user input.

    Convenience function that applies multiple security checks:
    1. Length validation
    2. HTML sanitization or stripping
    3. Additional safety checks

    Args:
        content: Raw user input
        allow_html: If True, sanitize HTML. If False, strip all HTML.
        max_length: Maximum allowed length (optional)
        field_name: Field name for error messages

    Returns:
        Sanitized and validated content

    Raises:
        ValidationError: If validation fails

    Example:
        >>> sanitize_and_validate("<p>Hello</p>", allow_html=True, max_length=100)
        "<p>Hello</p>"
        >>> sanitize_and_validate("<script>xss</script>", allow_html=False)
        ""
    """
    if not content:
        return content

    # Step 1: Check length BEFORE sanitization (prevent processing huge strings)
    if max_length:
        check_max_length(content, max_length, field_name)

    # Step 2: Sanitize
    if allow_html:
        sanitized = sanitize_html(content)
    else:
        sanitized = sanitize_plaintext(content)

    # Step 3: Log if significant content was removed (potential attack)
    original_len = len(content)
    sanitized_len = len(sanitized)
    if original_len > 0 and sanitized_len < original_len * 0.5:
        logger.warning(
            "significant_content_removed_during_sanitization",
            field=field_name,
            original_length=original_len,
            sanitized_length=sanitized_len,
            removed_percent=round((1 - sanitized_len / original_len) * 100, 2)
        )

    return sanitized
