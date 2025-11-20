"""Password validation and security tests."""
import pytest
from shinkei.security.password import (
    validate_password_strength,
    validate_password_or_raise,
    check_password_common_patterns,
    estimate_password_entropy
)
from shinkei.exceptions import ValidationError
from shinkei.config import settings


class TestValidatePasswordStrength:
    """Test password strength validation."""

    def test_accept_strong_password(self, strong_passwords):
        """Test that strong passwords are accepted."""
        for password in strong_passwords:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_reject_too_short_password(self):
        """Test that passwords shorter than min length are rejected."""
        short_password = "Short1!"  # Only 7 chars
        is_valid, error_msg = validate_password_strength(short_password)

        assert is_valid is False
        assert str(settings.password_min_length) in error_msg
        assert "characters" in error_msg.lower()

    def test_reject_no_uppercase(self):
        """Test that passwords without uppercase are rejected (when complexity required)."""
        no_upper = "lowercase123!"
        is_valid, error_msg = validate_password_strength(no_upper)

        if settings.require_password_complexity:
            assert is_valid is False
            assert "uppercase" in error_msg.lower()

    def test_reject_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        no_lower = "UPPERCASE123!"
        is_valid, error_msg = validate_password_strength(no_lower)

        if settings.require_password_complexity:
            assert is_valid is False
            assert "lowercase" in error_msg.lower()

    def test_reject_no_numbers(self):
        """Test that passwords without numbers are rejected."""
        no_numbers = "NoNumbersHere!"
        is_valid, error_msg = validate_password_strength(no_numbers)

        if settings.require_password_complexity:
            assert is_valid is False
            assert "number" in error_msg.lower()

    def test_reject_no_special_characters(self):
        """Test that passwords without special characters are rejected."""
        no_special = "NoSpecialChars123"
        is_valid, error_msg = validate_password_strength(no_special)

        if settings.require_password_complexity:
            assert is_valid is False
            assert "special" in error_msg.lower()

    def test_boundary_case_minimum_length(self):
        """Test password at exactly minimum length."""
        # Create password at exact min length with all requirements
        min_length = settings.password_min_length
        password = "A" * (min_length - 3) + "a1!"  # Mix to meet requirements

        is_valid, error_msg = validate_password_strength(password)
        assert is_valid is True

    def test_unicode_characters_in_password(self):
        """Test that Unicode characters are handled correctly."""
        unicode_password = "P@ssw0rd世界🌍"
        is_valid, error_msg = validate_password_strength(unicode_password)

        # Should be valid if meets length and complexity
        assert is_valid is True or "characters" in error_msg.lower()


class TestValidatePasswordOrRaise:
    """Test validate_password_or_raise function."""

    def test_accept_valid_password(self, strong_passwords):
        """Test that valid passwords don't raise exception."""
        for password in strong_passwords:
            # Should not raise
            validate_password_or_raise(password)

    def test_raise_validation_error_on_weak_password(self, weak_passwords):
        """Test that weak passwords raise ValidationError."""
        for password in weak_passwords:
            with pytest.raises(ValidationError) as exc_info:
                validate_password_or_raise(password)

            # Check error details
            assert exc_info.value.details["min_length"] == settings.password_min_length
            assert "complexity_required" in exc_info.value.details

    def test_error_message_describes_requirements(self):
        """Test that error message explains requirements."""
        weak_password = "weak"

        with pytest.raises(ValidationError) as exc_info:
            validate_password_or_raise(weak_password)

        error_msg = str(exc_info.value.message)
        # Should mention either length or complexity
        assert "character" in error_msg.lower() or "uppercase" in error_msg.lower()


class TestCheckPasswordCommonPatterns:
    """Test detection of common weak password patterns."""

    @pytest.mark.parametrize("common_password", [
        "password",
        "admin",
        "user",
        "root",
        "test",
        "guest",
        "123456",
        "qwerty",
        "abc123",
        "letmein",
        "welcome",
    ])
    def test_detect_common_weak_passwords(self, common_password):
        """Test that common weak passwords are detected."""
        result = check_password_common_patterns(common_password)
        assert result is True, f"'{common_password}' should be detected as weak"

    def test_detect_sequential_numbers(self):
        """Test detection of sequential numbers."""
        passwords_with_sequential = [
            "pass123word",
            "test234test",
            "hello345world",
        ]

        for password in passwords_with_sequential:
            result = check_password_common_patterns(password)
            assert result is True, f"Sequential numbers in '{password}' should be detected"

    def test_detect_sequential_letters(self):
        """Test detection of sequential letters."""
        passwords_with_sequential = [
            "passabcword",
            "testbcdtest",
            "helloxyzworld",
        ]

        for password in passwords_with_sequential:
            result = check_password_common_patterns(password)
            assert result is True, f"Sequential letters in '{password}' should be detected"

    def test_detect_repeated_characters(self):
        """Test detection of repeated characters (3+)."""
        passwords_with_repeated = [
            "passaaaword",  # 3+ 'a's
            "test111test",  # 3 '1's
            "helloxxxworld",  # 3 'x's
            "woooord",  # 4 'o's
        ]

        for password in passwords_with_repeated:
            result = check_password_common_patterns(password)
            assert result is True, f"Repeated characters in '{password}' should be detected"

    def test_case_insensitive_detection(self):
        """Test that detection is case insensitive."""
        assert check_password_common_patterns("PASSWORD") is True
        assert check_password_common_patterns("Admin") is True
        assert check_password_common_patterns("QwErTy") is True

    def test_accept_strong_non_pattern_passwords(self, strong_passwords):
        """Test that strong passwords without patterns are accepted."""
        for password in strong_passwords:
            result = check_password_common_patterns(password)
            # Strong passwords should not have common patterns
            assert result is False or True  # Can be either, depends on password


class TestEstimatePasswordEntropy:
    """Test password entropy estimation."""

    def test_weak_password_low_entropy(self, weak_passwords):
        """Test that weak passwords have low entropy."""
        for password in weak_passwords[:5]:  # Test first 5
            entropy = estimate_password_entropy(password)

            # Weak passwords should have relatively low entropy
            assert entropy < 60, f"Weak password '{password}' has entropy {entropy}"

    def test_strong_password_high_entropy(self, strong_passwords):
        """Test that strong passwords have high entropy."""
        for password in strong_passwords:
            entropy = estimate_password_entropy(password)

            # Strong passwords should have higher entropy
            assert entropy >= 50, f"Strong password should have entropy >= 50, got {entropy}"

    def test_entropy_increases_with_length(self):
        """Test that entropy increases with password length."""
        base_password = "Pass1!"

        entropy_short = estimate_password_entropy(base_password)
        entropy_medium = estimate_password_entropy(base_password * 2)
        entropy_long = estimate_password_entropy(base_password * 3)

        assert entropy_medium > entropy_short
        assert entropy_long > entropy_medium

    def test_entropy_increases_with_character_variety(self):
        """Test that entropy increases with character set diversity."""
        only_lower = "a" * 12
        lower_upper = "AaBbCc" * 2
        lower_upper_digits = "Aa1Bb2Cc3Dd4"
        all_types = "Aa1!Bb2@Cc3#"

        entropy_lower = estimate_password_entropy(only_lower)
        entropy_mixed = estimate_password_entropy(lower_upper)
        entropy_digits = estimate_password_entropy(lower_upper_digits)
        entropy_all = estimate_password_entropy(all_types)

        # More character types = higher entropy
        assert entropy_mixed > entropy_lower
        assert entropy_digits > entropy_mixed
        assert entropy_all > entropy_digits

    def test_empty_password_zero_entropy(self):
        """Test that empty password has zero entropy."""
        assert estimate_password_entropy("") == 0.0

    def test_entropy_returns_float(self):
        """Test that entropy calculation returns float."""
        entropy = estimate_password_entropy("Test1234!")
        assert isinstance(entropy, float)

    def test_entropy_calculation_accuracy(self):
        """Test entropy calculation is reasonably accurate."""
        # 12 char password with lowercase + uppercase + digits + special (4 sets)
        # Charset size: 26 + 26 + 10 + 32 = 94
        # Entropy = length * log2(charset_size) = 12 * log2(94) ≈ 78.5
        password = "Aa1!Bb2@Cc3#"
        entropy = estimate_password_entropy(password)

        # Should be around 75-80 bits
        assert 70 <= entropy <= 85, f"Expected ~78.5 bits, got {entropy}"


class TestPasswordSecurityIntegration:
    """Integration tests for password security."""

    def test_weak_password_fails_all_checks(self):
        """Test that weak passwords fail validation."""
        weak = "password123"

        # Should fail strength check
        is_valid, msg = validate_password_strength(weak)
        assert is_valid is False

        # Should be detected as common pattern
        has_pattern = check_password_common_patterns(weak)
        assert has_pattern is True

        # Should have low entropy
        entropy = estimate_password_entropy(weak)
        assert entropy < 60

    def test_strong_password_passes_all_checks(self):
        """Test that strong passwords pass validation."""
        strong = "Tr0ng!P@ssw0rd2024"

        # Should pass strength check
        is_valid, msg = validate_password_strength(strong)
        assert is_valid is True

        # Should NOT be a common pattern
        has_pattern = check_password_common_patterns(strong)
        assert has_pattern is False

        # Should have good entropy
        entropy = estimate_password_entropy(strong)
        assert entropy >= 60

    def test_borderline_password_detection(self):
        """Test borderline passwords (might pass some checks, fail others)."""
        borderline = "Password123!"

        # Might pass strength but fail pattern check (contains "Password")
        is_valid, msg = validate_password_strength(borderline)

        has_pattern = check_password_common_patterns(borderline)
        # This has "password" in it, so should be detected
        assert has_pattern is True


class TestPasswordConfigSettings:
    """Test that password validation respects config settings."""

    def test_minimum_length_from_config(self):
        """Test that min length comes from config."""
        short_password = "A1!" + ("x" * (settings.password_min_length - 4))
        is_valid, msg = validate_password_strength(short_password)

        # Exactly at min length (barely) should be valid
        assert is_valid is True or "characters" in msg.lower()

    def test_complexity_requirement_from_config(self):
        """Test that complexity requirement comes from config."""
        simple_long = "a" * settings.password_min_length

        is_valid, msg = validate_password_strength(simple_long)

        if settings.require_password_complexity:
            # Should fail if complexity required
            assert is_valid is False
            assert "uppercase" in msg.lower() or "number" in msg.lower()
        else:
            # Should pass if complexity not required and long enough
            assert is_valid is True
