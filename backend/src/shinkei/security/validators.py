"""Custom Pydantic validators for secure input handling."""
from typing import Optional, Annotated
from pydantic import AfterValidator, BeforeValidator, Field
from shinkei.security.sanitizers import (
    sanitize_html,
    sanitize_plaintext,
    validate_url,
    check_max_length
)


def _sanitize_html_validator(v: Optional[str]) -> Optional[str]:
    """Validator function to sanitize HTML content."""
    if v is None:
        return v
    return sanitize_html(v)


def _sanitize_plaintext_validator(v: Optional[str]) -> Optional[str]:
    """Validator function to strip all HTML."""
    if v is None:
        return v
    return sanitize_plaintext(v)


def _validate_url_validator(v: Optional[str]) -> Optional[str]:
    """Validator function for URLs."""
    if v is None:
        return v
    return validate_url(v)


def _max_length_validator(max_len: int):
    """Factory for max length validator."""
    def validator(v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return check_max_length(v, max_len, "field")
    return validator


# Pydantic v2 Annotated types for reusable validators

# SanitizedStr: Allows safe HTML formatting
# Use for: story synopsis, world backdrop, story beat content
SanitizedStr = Annotated[
    str,
    AfterValidator(_sanitize_html_validator)
]

# PlainStr: Strips all HTML, only plain text allowed
# Use for: titles, names, labels, tags
PlainStr = Annotated[
    str,
    AfterValidator(_sanitize_plaintext_validator)
]

# SafeURL: Validates URL scheme and format
# Use for: external links, references
SafeURL = Annotated[
    str,
    AfterValidator(_validate_url_validator)
]

# Factory function for length-limited strings
def LimitedStr(max_length: int):
    """
    Create a string type with maximum length validation.

    Args:
        max_length: Maximum allowed length

    Returns:
        Annotated string type with length validation

    Example:
        Title = LimitedStr(200)
        class MySchema(BaseModel):
            title: Title
    """
    return Annotated[
        str,
        Field(max_length=max_length),
        AfterValidator(_max_length_validator(max_length))
    ]


# Factory function for sanitized HTML with max length
def SanitizedHTML(max_length: int):
    """
    Create a sanitized HTML string type with maximum length.

    Combines HTML sanitization with length validation.

    Args:
        max_length: Maximum allowed length

    Returns:
        Annotated string type with sanitization and length validation

    Example:
        Synopsis = SanitizedHTML(5000)
        class StorySchema(BaseModel):
            synopsis: Synopsis
    """
    def combined_validator(v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # First check length, then sanitize
        v = check_max_length(v, max_length, "html_field")
        return sanitize_html(v)

    return Annotated[
        str,
        Field(max_length=max_length),
        AfterValidator(combined_validator)
    ]


# Factory function for plain text with max length
def PlainText(max_length: int):
    """
    Create a plain text string type with maximum length.

    Strips HTML and enforces length limit.

    Args:
        max_length: Maximum allowed length

    Returns:
        Annotated string type with HTML stripping and length validation

    Example:
        Title = PlainText(200)
        class WorldSchema(BaseModel):
            title: Title
    """
    def combined_validator(v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # First check length, then strip HTML
        v = check_max_length(v, max_length, "text_field")
        return sanitize_plaintext(v)

    return Annotated[
        str,
        Field(max_length=max_length),
        AfterValidator(combined_validator)
    ]


# Pydantic model validator for JSON fields
def sanitize_json_field(v):
    """
    Validator for JSON fields to sanitize nested string values.

    Use with Pydantic's field_validator decorator.

    Example:
        class MySchema(BaseModel):
            metadata: Dict[str, Any]

            @field_validator('metadata')
            @classmethod
            def sanitize_metadata(cls, v):
                return sanitize_json_field(v)
    """
    from shinkei.security.sanitizers import sanitize_json

    if v is None:
        return v
    return sanitize_json(v)
