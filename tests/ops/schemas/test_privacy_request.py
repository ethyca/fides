import pytest
from pydantic import ValidationError

from fides.api.db.seed import DEFAULT_ACCESS_POLICY
from fides.api.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestFilter,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)


class TestPrivacyRequestFilter:
    def test_single_status(self):
        params = PrivacyRequestFilter(status=PrivacyRequestStatus.pending)
        assert params.status == [PrivacyRequestStatus.pending]

    def test_list_of_statuses(self):
        params = PrivacyRequestFilter(
            status=[PrivacyRequestStatus.pending, PrivacyRequestStatus.complete]
        )
        assert params.status == [
            PrivacyRequestStatus.pending,
            PrivacyRequestStatus.complete,
        ]

    def test_none_status(self):
        params = PrivacyRequestFilter(status=None)
        assert params.status is None

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            PrivacyRequestFilter(status="invalid_status")


class TestPrivacyRequestCreate:
    def test_valid_source(self):
        PrivacyRequestCreate(
            **{
                "identity": {"email": "user@example.com"},
                "policy_key": DEFAULT_ACCESS_POLICY,
                "source": PrivacyRequestSource.privacy_center,
            }
        )

    def test_invalid_source(self):
        with pytest.raises(ValidationError):
            PrivacyRequestCreate(
                **{
                    "identity": {"email": "user@example.com"},
                    "policy_key": DEFAULT_ACCESS_POLICY,
                    "source": "Email",
                }
            )

    @pytest.mark.parametrize(
        "location",
        [
            "US",
            "US-CA",
            "GB",
            "CA-ON",
            "EEA",  # Standard formats
            "us",
            "us-ca",
            "eea",  # Lowercase
            "US_CA",
            "us_ny",
            "GB_SC",  # Underscores (should be normalized)
        ],
    )
    def test_valid_location_formats(self, location):
        """Test that various valid ISO 3166 location formats are accepted"""
        privacy_request = PrivacyRequestCreate(
            **{
                "identity": {"email": "user@example.com"},
                "policy_key": DEFAULT_ACCESS_POLICY,
                "location": location,
            }
        )
        # Verify location is normalized to uppercase with hyphens
        if location:
            assert privacy_request.location is not None
            assert privacy_request.location.isupper()
            assert "_" not in privacy_request.location

    @pytest.mark.parametrize(
        "location",
        [
            "USA",  # Too many characters for country code
            "U",  # Too few characters for country code
            "US-CALIFORNIA",  # Region code too long
            "US-",  # Empty region code
            "12",  # Numeric country code
            "US CA",  # Space instead of hyphen/underscore
            "",  # Empty string
        ],
    )
    def test_invalid_location_formats(self, location):
        """Test that invalid location formats raise ValidationError"""
        with pytest.raises(ValidationError):
            PrivacyRequestCreate(
                **{
                    "identity": {"email": "user@example.com"},
                    "policy_key": DEFAULT_ACCESS_POLICY,
                    "location": location,
                }
            )

    def test_none_location(self):
        """Test that None location is accepted (optional field)"""
        PrivacyRequestCreate(
            **{
                "identity": {"email": "user@example.com"},
                "policy_key": DEFAULT_ACCESS_POLICY,
                "location": None,
            }
        )

    def test_missing_location(self):
        """Test that missing location field is accepted (optional field)"""
        PrivacyRequestCreate(
            **{
                "identity": {"email": "user@example.com"},
                "policy_key": DEFAULT_ACCESS_POLICY,
            }
        )

    @pytest.mark.parametrize(
        "input_location,expected_output",
        [
            # (input, expected_output)
            ("us", "US"),
            ("US", "US"),
            ("us-ca", "US-CA"),
            ("US-CA", "US-CA"),
            ("us_ca", "US-CA"),  # Underscore converted to hyphen
            ("US_NY", "US-NY"),  # Underscore converted to hyphen
            ("eea", "EEA"),
            ("EEA", "EEA"),
            ("gb", "GB"),
            ("ca_on", "CA-ON"),  # Underscore with lowercase
        ],
    )
    def test_location_normalization(self, input_location, expected_output):
        """Test that location codes are properly normalized"""
        privacy_request = PrivacyRequestCreate(
            **{
                "identity": {"email": "user@example.com"},
                "policy_key": DEFAULT_ACCESS_POLICY,
                "location": input_location,
            }
        )
        assert privacy_request.location == expected_output
