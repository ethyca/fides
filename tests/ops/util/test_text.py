"""Tests for text utility functions."""

import pytest

from fides.api.util.text import normalize_location_code, to_snake_case


class TestNormalizeLocationCode:
    """Test location code normalization functionality."""

    def test_normalize_location_code_valid_cases(self):
        """Test that valid location codes are properly normalized."""
        test_cases = [
            # Basic country codes
            ("us", "US"),
            ("US", "US"),
            ("gb", "GB"),
            ("GB", "GB"),
            # Subdivision codes with hyphens
            ("us-ca", "US-CA"),
            ("US-CA", "US-CA"),
            ("ca-on", "CA-ON"),
            ("CA-ON", "CA-ON"),
            # Subdivision codes with underscores (should be converted)
            ("us_ca", "US-CA"),
            ("US_CA", "US-CA"),
            ("ca_on", "CA-ON"),
            ("CA_ON", "CA-ON"),
            ("us_ny", "US-NY"),
            ("US_NY", "US-NY"),
            # Special cases
            ("eea", "EEA"),
            ("EEA", "EEA"),
            ("Eea", "EEA"),
            # Mixed case with underscores
            ("Us_Ca", "US-CA"),
            ("gb_sc", "GB-SC"),
        ]

        for input_location, expected_output in test_cases:
            result = normalize_location_code(input_location)
            assert (
                result == expected_output
            ), f"Expected {expected_output}, got {result} for input {input_location}"

    def test_normalize_location_code_invalid_cases(self):
        """Test that invalid location codes raise ValueError."""
        invalid_cases = [
            "USA",  # Too many characters for country code
            "U",  # Too few characters for country code
            "US-CALIFORNIA",  # Region code too long
            "US-",  # Empty region code after hyphen
            "US_",  # Empty region code after underscore
            "12",  # Numeric country code
            "US CA",  # Space instead of separator
            "US+CA",  # Invalid separator
            "1US",  # Invalid country code starting with number
            "US-1234",  # Region code too long
        ]

        for invalid_location in invalid_cases:
            with pytest.raises(ValueError) as exc_info:
                normalize_location_code(invalid_location)
            assert "Invalid location format" in str(exc_info.value)

    def test_normalize_location_code_empty_input(self):
        """Test that empty input raises appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            normalize_location_code("")
        assert "Location code cannot be empty" in str(exc_info.value)

    def test_normalize_location_code_none_input(self):
        """Test that None input raises appropriate error."""
        with pytest.raises(ValueError):
            normalize_location_code(None)  # type: ignore


class TestToSnakeCase:
    """Test the existing to_snake_case function to ensure it still works."""

    def test_to_snake_case(self):
        """Test that to_snake_case works as expected."""
        test_cases = [
            ("foo bar", "foo_bar"),
            ("foo\nbar", "foo_bar"),
            ("foo\tbar", "foo_bar"),
            ("foo-bar", "foo_bar"),
            ("foo*bar", "foobar"),
        ]

        for input_text, expected_output in test_cases:
            result = to_snake_case(input_text)
            assert result == expected_output
