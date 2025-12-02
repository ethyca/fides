"""Unit tests for privacy_request schemas"""

import pytest
from pydantic import ValidationError

from fides.api.schemas.privacy_request import (
    PrivacyRequestBulkSelection,
    PrivacyRequestFilter,
    PrivacyRequestStatus,
)


class TestPrivacyRequestBulkSelection:
    """Test the PrivacyRequestBulkSelection schema validation"""

    @pytest.mark.parametrize(
        "request_ids,filters,exclude_ids,expected_request_ids,expected_filters,expected_exclude_ids",
        [
            # Valid: explicit request_ids only
            (
                ["req-1", "req-2", "req-3"],
                None,
                None,
                ["req-1", "req-2", "req-3"],
                None,
                None,
            ),
            # Valid: filters only
            (
                None,
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                None,
                None,
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                None,
            ),
            # Valid: filters with exclusions
            (
                None,
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                ["req-1", "req-2"],
                None,
                PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
                ["req-1", "req-2"],
            ),
            # Valid: empty filters with exclusions (select all except excluded)
            (
                None,
                PrivacyRequestFilter(),
                ["req-1", "req-2"],
                None,
                PrivacyRequestFilter(),
                ["req-1", "req-2"],
            ),
            # Valid: request_ids with exclude_ids=None
            (
                ["req-1"],
                None,
                None,
                ["req-1"],
                None,
                None,
            ),
            # Valid: request_ids with empty exclude_ids list (not considered as passed)
            (
                ["req-1"],
                None,
                [],
                ["req-1"],
                None,
                [],
            ),
            # Valid: request_ids with filters=None
            (
                ["req-1"],
                None,
                None,
                ["req-1"],
                None,
                None,
            ),
        ],
    )
    def test_valid_selections(
        self,
        request_ids,
        filters,
        exclude_ids,
        expected_request_ids,
        expected_filters,
        expected_exclude_ids,
    ):
        """Test valid PrivacyRequestBulkSelection configurations"""
        selection = PrivacyRequestBulkSelection(
            request_ids=request_ids, filters=filters, exclude_ids=exclude_ids
        )
        assert selection.request_ids == expected_request_ids
        assert selection.filters == expected_filters
        assert selection.exclude_ids == expected_exclude_ids

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
