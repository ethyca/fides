"""Unit tests for utility functions in privacy_request_endpoints.py"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from fides.api.api.v1.endpoints.privacy_request_endpoints import (
    _resolve_request_ids_from_filters,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    PrivacyRequestBulkSelection,
    PrivacyRequestFilter,
    PrivacyRequestStatus,
)


class TestResolveRequestIdsFromFilters:
    """Test the _resolve_request_ids_from_filters utility function"""

    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_explicit_request_ids(self, mock_filter_queryset, db):
        """Test that explicit request_ids are returned directly without querying"""
        request_ids = ["req-1", "req-2", "req-3"]
        selection = PrivacyRequestBulkSelection(request_ids=request_ids)

        result = _resolve_request_ids_from_filters(db, selection)

        assert result == request_ids
        # Should not call the filter function when request_ids is provided
        mock_filter_queryset.assert_not_called()

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_filters_with_status(self, mock_filter_queryset, mock_privacy_request, db):
        """Test that filters are passed to _filter_privacy_request_queryset correctly"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_filter_queryset.return_value = mock_query

        # Mock the final query result
        mock_query.with_entities.return_value.all.return_value = [
            ("pri_123",),
            ("pri_456",),
        ]

        filters = PrivacyRequestFilter(status=PrivacyRequestStatus.pending)
        selection = PrivacyRequestBulkSelection(filters=filters)

        result = _resolve_request_ids_from_filters(db, selection)

        # Verify the filter function was called with correct parameters
        mock_filter_queryset.assert_called_once()
        call_kwargs = mock_filter_queryset.call_args[1]
        assert call_kwargs["status"] == [PrivacyRequestStatus.pending]

        # Verify results
        assert result == ["pri_123", "pri_456"]

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_filters_with_multiple_parameters(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that multiple filter parameters are all passed correctly"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_filter_queryset.return_value = mock_query

        mock_query.with_entities.return_value.all.return_value = [("pri_789",)]

        now = datetime.now(timezone.utc)
        filters = PrivacyRequestFilter(
            status=[PrivacyRequestStatus.pending, PrivacyRequestStatus.approved],
            external_id="ext-123",
            location="US",
            action_type=ActionType.access,
            created_gt=now,
        )
        selection = PrivacyRequestBulkSelection(filters=filters)

        result = _resolve_request_ids_from_filters(db, selection)

        # Verify all filter parameters were passed
        call_kwargs = mock_filter_queryset.call_args[1]
        assert call_kwargs["status"] == [
            PrivacyRequestStatus.pending,
            PrivacyRequestStatus.approved,
        ]
        assert call_kwargs["external_id"] == "ext-123"
        assert call_kwargs["location"] == "US"
        assert call_kwargs["action_type"] == ActionType.access
        assert call_kwargs["created_gt"] == now

        assert result == ["pri_789"]

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_filters_with_exclusions(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that exclude_ids are properly applied to filter results"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_filter_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_privacy_request.id = MagicMock()  # Mock the id column for the filter
        mock_filter_queryset.return_value = mock_filter_query

        # Mock filter to return the filtered query
        mock_filter_query.filter.return_value = mock_filter_query
        mock_filter_query.with_entities.return_value.all.return_value = [
            ("pri_222",),
            ("pri_333",),
        ]

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
            exclude_ids=["pri_111"],
        )

        result = _resolve_request_ids_from_filters(db, selection)

        # Verify that filter was called to exclude IDs
        mock_filter_query.filter.assert_called_once()

        # Results should not include excluded ID
        assert result == ["pri_222", "pri_333"]
        assert "pri_111" not in result

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_filters_with_multiple_exclusions(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test filtering with multiple IDs in exclude_ids"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_filter_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_privacy_request.id = MagicMock()
        mock_filter_queryset.return_value = mock_filter_query

        mock_filter_query.filter.return_value = mock_filter_query
        mock_filter_query.with_entities.return_value.all.return_value = [
            ("pri_333",),
            ("pri_444",),
            ("pri_555",),
        ]

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
            exclude_ids=["pri_111", "pri_222"],
        )

        result = _resolve_request_ids_from_filters(db, selection)

        # Verify filter was called for exclusions
        mock_filter_query.filter.assert_called_once()

        # Results should have 3 items, excluding the two IDs
        assert len(result) == 3
        assert result == ["pri_333", "pri_444", "pri_555"]

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_filters_no_results_raises_exception(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that HTTPException is raised when filters return no results"""
        # Mock the query chain to return empty results
        mock_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_filter_queryset.return_value = mock_query

        # Return empty list
        mock_query.with_entities.return_value.all.return_value = []

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.canceled)
        )

        with pytest.raises(HTTPException) as exc_info:
            _resolve_request_ids_from_filters(db, selection)

        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert (
            "No privacy requests found matching the provided filters."
            in exc_info.value.detail
        )

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_filters_all_excluded_raises_exception(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that HTTPException is raised when all matching results are excluded"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_filter_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_privacy_request.id = MagicMock()
        mock_filter_queryset.return_value = mock_filter_query

        # After exclusion, no results remain
        mock_filter_query.filter.return_value = mock_filter_query
        mock_filter_query.with_entities.return_value.all.return_value = []

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.pending),
            exclude_ids=["pri_111", "pri_222"],
        )

        with pytest.raises(HTTPException) as exc_info:
            _resolve_request_ids_from_filters(db, selection)

        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert (
            "No privacy requests found matching the provided filters."
            in exc_info.value.detail
        )

    @patch("fides.api.api.v1.endpoints.privacy_request_endpoints.PrivacyRequest")
    @patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints._filter_privacy_request_queryset"
    )
    def test_query_without_large_columns_called(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that PrivacyRequest.query_without_large_columns is called to build the base query"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_filter_queryset.return_value = mock_query

        mock_query.with_entities.return_value.all.return_value = [("pri_abc",)]

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.pending)
        )

        _resolve_request_ids_from_filters(db, selection)

        # Verify query_without_large_columns was called with db
        mock_privacy_request.query_without_large_columns.assert_called_once_with(db)
