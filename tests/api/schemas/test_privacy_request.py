"""Unit tests for privacy_request schemas"""

import pytest
from pydantic import ValidationError

from fides.api.db.seed import DEFAULT_ACCESS_POLICY
from fides.api.schemas.privacy_request import (
    PrivacyRequestBulkSelection,
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


class TestPrivacyRequestBulkSelection:
    """Test the PrivacyRequestBulkSelection schema validation"""

    @pytest.mark.parametrize(
        "request_ids,filters,exclude_ids",
        [
            # Valid: explicit request_ids only
            (
                ["req-1", "req-2", "req-3"],
                None,
                None,
            ),
            # Valid: request_ids with empty exclude_ids list (not considered as passed)
            (
                ["req-1"],
                None,
                [],
            ),
            # Valid: filters only
            (
                None,
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                None,
            ),
            # Valid: filters with exclusions
            (
                None,
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                ["req-1", "req-2"],
            ),
            # Valid: empty filters with exclusions (select all except excluded)
            (
                None,
                PrivacyRequestFilter(),
                ["req-1", "req-2"],
            ),
        ],
    )
    def test_valid_selections(
        self,
        request_ids,
        filters,
        exclude_ids,
    ):
        """Test valid PrivacyRequestBulkSelection configurations"""
        selection = PrivacyRequestBulkSelection(
            request_ids=request_ids, filters=filters, exclude_ids=exclude_ids
        )
        assert selection.request_ids == request_ids
        assert selection.filters == filters
        assert selection.exclude_ids == exclude_ids

    @pytest.mark.parametrize(
        "request_ids,filters,exclude_ids,expected_error_msg",
        [
            # Error: neither request_ids nor filters provided
            (
                None,
                None,
                None,
                "At least one of 'request_ids' or 'filters' must be provided",
            ),
            # Error: empty request_ids list
            (
                [],
                None,
                None,
                "'request_ids' cannot be empty",
            ),
            # Error: both request_ids and filters provided (mutually exclusive)
            (
                ["req-1"],
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                None,
                "'request_ids' and 'filters' are mutually exclusive",
            ),
            # Error: exclude_ids with request_ids
            (
                ["req-1", "req-2"],
                None,
                ["req-3"],
                "'exclude_ids' can only be used with 'filters', not with 'request_ids'",
            ),
        ],
    )
    def test_validation_errors(
        self, request_ids, filters, exclude_ids, expected_error_msg
    ):
        """Test validation errors for invalid PrivacyRequestBulkSelection configurations"""
        with pytest.raises(ValidationError) as exc_info:
            PrivacyRequestBulkSelection(
                request_ids=request_ids, filters=filters, exclude_ids=exclude_ids
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert expected_error_msg in errors[0]["msg"]
