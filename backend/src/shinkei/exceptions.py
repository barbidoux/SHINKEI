"""Custom exceptions for Shinkei backend."""
from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class ShinkeiException(Exception):
    """Base exception for all Shinkei custom exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ShinkeiException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details or {}
        )


class AuthorizationError(ShinkeiException):
    """Raised when user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {}
        )


class ResourceNotFoundError(ShinkeiException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found: {resource_id}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"resource": resource, "resource_id": resource_id}
        )


class ValidationError(ShinkeiException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=error_details
        )


class RateLimitError(ShinkeiException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details or {}
        )


class DatabaseError(ShinkeiException):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {}
        )


class ExternalServiceError(ShinkeiException):
    """Raised when an external service (AI providers, Supabase) fails."""

    def __init__(
        self,
        service: str,
        message: str = "External service unavailable",
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["service"] = service
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details
        )


def create_error_response(
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    error_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details (sanitized)
        error_type: Type of error (e.g., "validation_error", "authentication_error")

    Returns:
        Dictionary with error information
    """
    response = {
        "error": {
            "message": message,
            "type": error_type or "error",
            "status_code": status_code
        }
    }

    # Only include details if provided and not in production
    # In production, detailed errors should only be logged, not returned to client
    if details:
        response["error"]["details"] = details

    return response
