"""Shared fixtures for security tests."""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from shinkei.config import settings


@pytest.fixture
def valid_access_token():
    """Generate a valid access token for testing."""
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": "test-user-id",
            "exp": now + timedelta(minutes=30),
            "iat": now - timedelta(seconds=5),  # Issued 5 seconds ago to avoid clock skew
            "type": "access"
        },
        settings.secret_key,
        algorithm=settings.algorithm
    )


@pytest.fixture
def expired_access_token():
    """Generate an expired access token."""
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": "test-user-id",
            "exp": now - timedelta(minutes=10),  # Expired 10 minutes ago
            "iat": now - timedelta(minutes=40),  # Issued 40 minutes ago
            "type": "access"
        },
        settings.secret_key,
        algorithm=settings.algorithm
    )


@pytest.fixture
def future_issued_token():
    """Generate a token with future issued-at time (invalid)."""
    return jwt.encode(
        {
            "sub": "test-user-id",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow() + timedelta(minutes=5),  # Future iat
            "type": "access"
        },
        settings.secret_key,
        algorithm=settings.algorithm
    )


@pytest.fixture
def refresh_token():
    """Generate a valid refresh token (wrong type for API calls)."""
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": "test-user-id",
            "exp": now + timedelta(days=7),
            "iat": now - timedelta(seconds=5),  # Issued 5 seconds ago
            "type": "refresh"
        },
        settings.secret_key,
        algorithm=settings.algorithm
    )


@pytest.fixture
def token_without_sub():
    """Generate a token missing the 'sub' claim."""
    return jwt.encode(
        {
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "type": "access"
        },
        settings.secret_key,
        algorithm=settings.algorithm
    )


@pytest.fixture
def malformed_tokens():
    """Return a list of malformed JWT tokens for testing."""
    return [
        "not.a.valid.jwt.token",
        "header.payload",  # Missing signature
        "",  # Empty string
        "eyJhbGciOiJub25lIn0.eyJzdWIiOiJ1c2VyIn0.",  # "none" algorithm attempt
        "x" * 500,  # Random string
    ]


@pytest.fixture
def xss_payloads():
    """Common XSS attack payloads for testing input sanitization."""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
        "<IMG SRC=\"javascript:alert('XSS');\">",
        "<IMG SRC=JaVaScRiPt:alert('XSS')>",
        "<IFRAME SRC=\"javascript:alert('XSS');\"></IFRAME>",
        "<svg/onload=alert('XSS')>",
        "<img src=x:alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "<marquee onstart=alert('XSS')>",
        "&lt;script&gt;alert('XSS')&lt;/script&gt;",  # HTML entities
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",  # Numeric entities
        "\u003cscript\u003ealert('XSS')\u003c/script\u003e",  # Unicode
        "<a href=\"javascript:alert('XSS')\">Click</a>",
        "<div onmouseover='alert(\"XSS\")'>Hover</div>",
    ]


@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection payloads for testing."""
    return [
        "'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "1 UNION SELECT * FROM users",
        "' OR 1=1--",
        "admin'--",
        "1' AND '1'='1",
        "' OR 'a'='a",
        "x' AND email IS NOT NULL; --",
        "1'; EXEC sp_executesql N'DROP TABLE users'; --",
    ]


@pytest.fixture
def weak_passwords():
    """Common weak passwords for testing password validation."""
    return [
        "password",
        "123456",
        "qwerty",
        "admin",
        "letmein",
        "welcome",
        "Password123",  # Common pattern
        "12345678",
        "abc123",
        "password1",
        "Passw0rd",  # Predictable
        "aaaaaa11",  # Repeated characters
        "abcd1234",  # Sequential
        "Test1234",  # Dictionary word + numbers
    ]


@pytest.fixture
def strong_passwords():
    """Strong passwords that should pass validation."""
    return [
        "Tr0ng!P@ssw0rd2024",
        "My$ecur3P@ssphrase!",
        "c0mpl3x!ty#2024Secure",
        "9X#mK2$vL@pQw5nZ",
        "Sup3r$ecureP@ss!2024",
        "Compl3x&Str0ng#Pass",
    ]


@pytest.fixture
def auth_headers(valid_access_token):
    """Generate authorization headers with valid token."""
    return {"Authorization": f"Bearer {valid_access_token}"}


@pytest.fixture
def expired_auth_headers(expired_access_token):
    """Generate authorization headers with expired token."""
    return {"Authorization": f"Bearer {expired_access_token}"}


@pytest.fixture
def malicious_json_payloads():
    """Malicious JSON payloads for deserialization testing."""
    # Deeply nested JSON (100 levels)
    deeply_nested = {}
    current = deeply_nested
    for i in range(100):
        current["nested"] = {}
        current = current["nested"]

    return [
        deeply_nested,  # Too deep
        {"huge_array": ["x"] * 100000},  # Huge array
        {"name": ["not", "a", "string"]},  # Wrong type
        {"user_id": {"nested": "object"}},  # Unexpected nesting
    ]


@pytest.fixture
def dangerous_urls():
    """Dangerous URLs that should be rejected."""
    return [
        "javascript:alert('XSS')",
        "data:text/html,<script>alert('XSS')</script>",
        "file:///etc/passwd",
        "vbscript:msgbox('XSS')",
        "about:blank",
        "javascript:void(0)",
    ]


@pytest.fixture
def safe_urls():
    """Safe URLs that should be accepted."""
    return [
        "https://example.com",
        "http://localhost:3000",
        "https://api.shinkei.app/worlds",
        "http://127.0.0.1:8000/api/v1/health",
    ]
