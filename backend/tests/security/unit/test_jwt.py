"""JWT security tests."""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from shinkei.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_not_blacklisted,
    extract_user_id,
    get_token_expiration,
    is_token_expired
)
from shinkei.exceptions import AuthenticationError
from shinkei.config import settings


class TestCreateAccessToken:
    """Test access token creation."""

    def test_creates_valid_jwt(self):
        """Test that create_access_token generates a valid JWT."""
        token = create_access_token("user-123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_contains_required_claims(self):
        """Test that token contains all required claims."""
        token = create_access_token("user-123")

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert "sub" in payload
        assert payload["sub"] == "user-123"
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload

    def test_token_type_is_access(self):
        """Test that token type is 'access'."""
        token = create_access_token("user-123")

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert payload["type"] == "access"

    def test_default_expiration_time(self):
        """Test that default expiration is configured value."""
        token = create_access_token("user-123")

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        exp_delta = exp_time - iat_time

        # Should be approximately access_token_expire_minutes
        expected_minutes = settings.access_token_expire_minutes
        assert abs(exp_delta.total_seconds() / 60 - expected_minutes) < 1

    def test_custom_expiration_time(self):
        """Test custom expiration time."""
        custom_delta = timedelta(minutes=15)
        token = create_access_token("user-123", expires_delta=custom_delta)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        exp_delta = exp_time - iat_time

        # Should be approximately 15 minutes
        assert abs(exp_delta.total_seconds() / 60 - 15) < 1

    def test_additional_claims_included(self):
        """Test that additional claims are included in token."""
        additional = {"role": "admin", "permissions": ["read", "write"]}
        token = create_access_token("user-123", additional_claims=additional)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_correct_algorithm_used(self):
        """Test that configured algorithm is used."""
        token = create_access_token("user-123")

        # Decode header to check algorithm
        header = jwt.get_unverified_header(token)
        assert header["alg"] == settings.algorithm


class TestCreateRefreshToken:
    """Test refresh token creation."""

    def test_creates_valid_refresh_token(self):
        """Test that create_refresh_token generates a valid JWT."""
        token = create_refresh_token("user-123")

        assert token is not None
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_token_type_is_refresh(self):
        """Test that token type is 'refresh'."""
        token = create_refresh_token("user-123")

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        assert payload["type"] == "refresh"

    def test_longer_expiration_than_access(self):
        """Test that refresh token has longer expiration."""
        access_token = create_access_token("user-123")
        refresh_token = create_refresh_token("user-123")

        access_payload = jwt.decode(
            access_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        refresh_payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        access_exp = datetime.fromtimestamp(access_payload["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])

        assert refresh_exp > access_exp

    def test_refresh_expiration_days(self):
        """Test that refresh token expires after configured days."""
        token = create_refresh_token("user-123")

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        exp_delta = exp_time - iat_time

        # Should be approximately refresh_token_expire_days
        expected_days = settings.refresh_token_expire_days
        assert abs(exp_delta.days - expected_days) <= 1


class TestDecodeToken:
    """Test token decoding and validation."""

    def test_decode_valid_access_token(self, valid_access_token):
        """Test decoding a valid access token."""
        payload = decode_token(valid_access_token, expected_type="access")

        assert payload["sub"] == "test-user-id"
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self, refresh_token):
        """Test decoding a valid refresh token."""
        payload = decode_token(refresh_token, expected_type="refresh")

        assert payload["sub"] == "test-user-id"
        assert payload["type"] == "refresh"

    def test_reject_expired_token(self, expired_access_token):
        """Test that expired tokens are rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(expired_access_token)

        assert "expired" in str(exc_info.value.message).lower()
        assert exc_info.value.details.get("expired") is True

    def test_reject_wrong_token_type(self, refresh_token):
        """Test that wrong token type is rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(refresh_token, expected_type="access")

        assert "type" in str(exc_info.value.message).lower()
        assert exc_info.value.details.get("token_type") == "refresh"

    def test_reject_missing_sub_claim(self, token_without_sub):
        """Test that tokens missing 'sub' claim are rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(token_without_sub)

        assert "sub" in str(exc_info.value.message).lower()

    def test_reject_future_issued_at_time(self, future_issued_token):
        """Test that tokens with future issued-at time are rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(future_issued_token)

        assert "future" in str(exc_info.value.message).lower()

    def test_reject_invalid_signature(self, valid_access_token):
        """Test that tokens with invalid signature are rejected."""
        # Tamper with the token
        parts = valid_access_token.split(".")
        tampered_token = parts[0] + "." + parts[1] + ".INVALID_SIGNATURE"

        with pytest.raises(AuthenticationError) as exc_info:
            decode_token(tampered_token)

        assert "validate" in str(exc_info.value.message).lower()

    @pytest.mark.parametrize("malformed_token", [
        "not.a.jwt",
        "header.payload",
        "",
        "x" * 500,
    ])
    def test_reject_malformed_tokens(self, malformed_token):
        """Test that malformed tokens are rejected."""
        with pytest.raises(AuthenticationError):
            decode_token(malformed_token)

    def test_verify_expiration_optional(self, expired_access_token):
        """Test that expiration verification can be disabled."""
        # Should not raise error when verify_expiration=False
        payload = decode_token(
            expired_access_token,
            expected_type="access",
            verify_expiration=False
        )

        assert payload["sub"] == "test-user-id"

    def test_none_algorithm_attack_prevented(self):
        """Test that 'none' algorithm attack is prevented."""
        # Attempt to create token with 'none' algorithm
        malicious_token = jwt.encode(
            {"sub": "attacker", "type": "access"},
            "",  # No key
            algorithm="none"
        )

        with pytest.raises(AuthenticationError):
            decode_token(malicious_token)


class TestVerifyTokenNotBlacklisted:
    """Test token blacklist verification."""

    def test_returns_true_placeholder(self, valid_access_token):
        """Test that placeholder implementation returns True."""
        # This is a placeholder - should be implemented with Redis in production
        result = verify_token_not_blacklisted(valid_access_token)

        assert result is True

    # TODO: Implement actual blacklist tests when Redis-based blacklist is added


class TestExtractUserId:
    """Test user ID extraction from tokens."""

    def test_extract_from_valid_token(self, valid_access_token):
        """Test extracting user ID from valid token."""
        user_id = extract_user_id(valid_access_token)

        assert user_id == "test-user-id"

    def test_extract_from_expired_token(self, expired_access_token):
        """Test extracting user ID from expired token (no validation)."""
        user_id = extract_user_id(expired_access_token)

        # Should still extract ID without validation
        assert user_id == "test-user-id"

    @pytest.mark.parametrize("malformed_token", [
        "not.a.jwt",
        "",
        "x" * 500,
    ])
    def test_return_unknown_for_invalid_token(self, malformed_token):
        """Test that 'unknown' is returned for invalid tokens."""
        user_id = extract_user_id(malformed_token)

        assert user_id == "unknown"


class TestGetTokenExpiration:
    """Test token expiration extraction."""

    def test_extract_expiration_from_valid_token(self, valid_access_token):
        """Test extracting expiration from valid token."""
        expiration = get_token_expiration(valid_access_token)

        assert expiration is not None
        assert isinstance(expiration, datetime)
        assert expiration > datetime.utcnow()  # Should be in future

    def test_extract_expiration_from_expired_token(self, expired_access_token):
        """Test extracting expiration from expired token."""
        expiration = get_token_expiration(expired_access_token)

        assert expiration is not None
        assert expiration < datetime.utcnow()  # Should be in past

    @pytest.mark.parametrize("malformed_token", [
        "not.a.jwt",
        "",
        "x" * 500,
    ])
    def test_return_none_for_invalid_token(self, malformed_token):
        """Test that None is returned for invalid tokens."""
        expiration = get_token_expiration(malformed_token)

        assert expiration is None


class TestIsTokenExpired:
    """Test token expiration checking."""

    def test_returns_false_for_valid_token(self, valid_access_token):
        """Test that valid token is not expired."""
        is_expired = is_token_expired(valid_access_token)

        assert is_expired is False

    def test_returns_true_for_expired_token(self, expired_access_token):
        """Test that expired token is detected."""
        is_expired = is_token_expired(expired_access_token)

        assert is_expired is True

    @pytest.mark.parametrize("malformed_token", [
        "not.a.jwt",
        "",
        "x" * 500,
    ])
    def test_returns_true_for_invalid_token(self, malformed_token):
        """Test that invalid tokens are considered expired."""
        is_expired = is_token_expired(malformed_token)

        assert is_expired is True

    def test_boundary_case_just_expired(self):
        """Test token that just expired."""
        # Create token that expires in 1 second
        token = create_access_token(
            "user-123",
            expires_delta=timedelta(seconds=1)
        )

        # Should not be expired yet
        assert is_token_expired(token) is False

        # Wait for expiration
        import time
        time.sleep(2)

        # Should now be expired
        assert is_token_expired(token) is True
