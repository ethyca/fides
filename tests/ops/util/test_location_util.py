"""Tests for location utility functions."""

import pytest

from fides.api.util.location_util import convert_location_to_display_name


class TestConvertLocationToDisplayName:
    """Test the convert_location_to_display_name function."""

    def test_country_codes(self):
        """Test conversion of country codes to display names."""
        # Test some common country codes
        assert convert_location_to_display_name("US") == "United States"
        assert convert_location_to_display_name("GB") == "United Kingdom"
        assert convert_location_to_display_name("CA") == "Canada"
        assert convert_location_to_display_name("DE") == "Germany"
        assert convert_location_to_display_name("FR") == "France"

        # Test lowercase input
        assert convert_location_to_display_name("us") == "United States"
        assert convert_location_to_display_name("gb") == "United Kingdom"

    def test_us_subdivision_codes(self):
        """Test conversion of US subdivision codes."""
        assert convert_location_to_display_name("US-CA") == "United States (California)"
        assert convert_location_to_display_name("US-NY") == "United States (New York)"
        assert convert_location_to_display_name("US-TX") == "United States (Texas)"
        assert convert_location_to_display_name("US-FL") == "United States (Florida)"

        # Test lowercase input
        assert convert_location_to_display_name("us-ca") == "United States (California)"

    def test_canadian_subdivision_codes(self):
        """Test conversion of Canadian subdivision codes."""
        assert convert_location_to_display_name("CA-ON") == "Canada (Ontario)"
        assert convert_location_to_display_name("CA-BC") == "Canada (British Columbia)"
        assert convert_location_to_display_name("CA-QC") == "Canada (Quebec)"
        assert convert_location_to_display_name("CA-AB") == "Canada (Alberta)"

    def test_uk_subdivision_codes(self):
        """Test conversion of UK subdivision codes."""
        assert convert_location_to_display_name("GB-ENG") == "England"
        assert convert_location_to_display_name("GB-SCT") == "Scotland"
        assert convert_location_to_display_name("GB-WAL") == "Wales"
        assert convert_location_to_display_name("GB-NIR") == "Northern Ireland"

    def test_special_codes(self):
        """Test conversion of special codes."""
        assert convert_location_to_display_name("EEA") == "European Economic Area"
        assert convert_location_to_display_name("eea") == "European Economic Area"

    def test_unknown_country_code(self):
        """Test handling of unknown country codes."""
        # Unknown country code should return the original code
        assert convert_location_to_display_name("ZZ") == "ZZ"
        assert convert_location_to_display_name("XX-YY") == "XX-YY"

    def test_unknown_subdivision_with_known_country(self):
        """Test subdivision code with known country but unknown subdivision."""
        # Should return country name with subdivision code in parentheses
        result = convert_location_to_display_name("US-ZZ")
        assert result == "United States (ZZ)"

        result = convert_location_to_display_name("CA-ZZ")
        assert result == "Canada (ZZ)"

    def test_case_insensitive(self):
        """Test that function handles various cases correctly."""
        # Mixed case input
        assert convert_location_to_display_name("Us") == "United States"
        assert convert_location_to_display_name("uS-ca") == "United States (California)"
        assert convert_location_to_display_name("GB-eng") == "England"
        assert convert_location_to_display_name("EeA") == "European Economic Area"
