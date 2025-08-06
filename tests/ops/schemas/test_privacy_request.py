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

    def test_valid_location_formats(self):
        """Test that various valid ISO 3166 location formats are accepted"""
        valid_locations = ["US", "US-CA", "GB", "CA-ON", "EEA", "us", "us-ca", "eea"]

        for location in valid_locations:
            PrivacyRequestCreate(
                **{
                    "identity": {"email": "user@example.com"},
                    "policy_key": DEFAULT_ACCESS_POLICY,
                    "location": location,
                }
            )

    def test_invalid_location_formats(self):
        """Test that invalid location formats raise ValidationError"""
        invalid_locations = [
            "USA",  # Too many characters for country code
            "U",  # Too few characters for country code
            "US-CALIFORNIA",  # Region code too long
            "US-",  # Empty region code
            "12",  # Numeric country code
            "US CA",  # Space instead of hyphen
            "US_CA",  # Underscore instead of hyphen
            "",  # Empty string
        ]

        for location in invalid_locations:
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


class TestPrivacyRequestResponse:
    """Test the PrivacyRequestResponse schema."""

    def test_location_display_name_serialization(self, policy):
        """Test that location_display_name is properly serialized from location field."""
        from fides.api.schemas.policy import PolicyResponse
        from fides.api.schemas.privacy_request import PrivacyRequestResponse

        # Test with US country code
        response_data = {
            "id": "test_id",
            "status": "pending",
            "location": "US",
            "policy": PolicyResponse.model_validate(policy),
        }
        response = PrivacyRequestResponse(**response_data)
        # The serializer should compute the display name
        serialized = response.model_dump()
        assert serialized["location_display_name"] == "United States"

        # Test with US subdivision code
        response_data["location"] = "US-CA"
        response = PrivacyRequestResponse(**response_data)
        serialized = response.model_dump()
        assert serialized["location_display_name"] == "United States (California)"

        # Test with special EEA code
        response_data["location"] = "EEA"
        response = PrivacyRequestResponse(**response_data)
        serialized = response.model_dump()
        assert serialized["location_display_name"] == "European Economic Area"

    def test_location_display_name_with_null_location(self, policy):
        """Test that location_display_name is None when location is None."""
        from fides.api.schemas.policy import PolicyResponse
        from fides.api.schemas.privacy_request import PrivacyRequestResponse

        response_data = {
            "id": "test_id",
            "status": "pending",
            "location": None,
            "policy": PolicyResponse.model_validate(policy),
        }
        response = PrivacyRequestResponse(**response_data)
        serialized = response.model_dump()
        assert serialized["location_display_name"] is None

    def test_location_display_name_explicit_value(self, policy):
        """Test that explicitly set location_display_name is preserved."""
        from fides.api.schemas.policy import PolicyResponse
        from fides.api.schemas.privacy_request import PrivacyRequestResponse

        response_data = {
            "id": "test_id",
            "status": "pending",
            "location": "US",
            "location_display_name": "Custom Display Name",
            "policy": PolicyResponse.model_validate(policy),
        }
        response = PrivacyRequestResponse(**response_data)
        serialized = response.model_dump()
        # Should preserve the explicitly set value
        assert serialized["location_display_name"] == "Custom Display Name"
