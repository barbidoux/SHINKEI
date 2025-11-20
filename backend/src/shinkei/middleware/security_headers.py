"""Security headers middleware for production-grade security."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from shinkei.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements OWASP recommended security headers:
    - HSTS: Force HTTPS in production
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response: Response = await call_next(request)

        # Strict-Transport-Security (HSTS)
        # Only enable in production to force HTTPS
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # X-Content-Type-Options
        # Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        # Prevents clickjacking by disallowing embedding in frames
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection
        # Enables browser's XSS filter (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content-Security-Policy
        # Restricts resource loading to prevent XSS
        # Configured for API-only backend (no inline scripts/styles)
        csp_directives = [
            "default-src 'none'",  # Block all by default
            "script-src 'none'",  # No scripts (API only)
            "style-src 'none'",  # No styles (API only)
            "img-src 'none'",  # No images (API only)
            "font-src 'none'",  # No fonts (API only)
            "connect-src 'self'",  # Allow API calls to same origin
            "frame-ancestors 'none'",  # Don't allow framing (redundant with X-Frame-Options)
            "base-uri 'self'",  # Restrict base tag to same origin
            "form-action 'self'",  # Only allow forms to submit to same origin
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer-Policy
        # Controls referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy)
        # Disables unnecessary browser features
        permissions = [
            "geolocation=()",  # No geolocation
            "microphone=()",  # No microphone
            "camera=()",  # No camera
            "payment=()",  # No payment APIs
            "usb=()",  # No USB access
            "magnetometer=()",  # No magnetometer
            "accelerometer=()",  # No accelerometer
            "gyroscope=()",  # No gyroscope
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # X-Powered-By removal (if present)
        # Don't advertise the technology stack
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        if "Server" in response.headers:
            del response.headers["Server"]

        return response
