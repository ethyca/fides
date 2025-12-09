"""Unit tests for utility functions in privacy_request_endpoints.py"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    MAX_BULK_FILTER_RESULTS,
    PrivacyRequestBulkSelection,
    PrivacyRequestFilter,
    PrivacyRequestStatus,
)
from fides.service.privacy_request.privacy_request_query_utils import (
    resolve_request_ids_from_filters,
)


@pytest.fixture(scope="module")
def celery_use_virtual_worker():
    """
    Override the session-scoped autouse fixture to prevent
    celery worker from being started for these unit tests.
    These tests only mock functions and don't need a worker.
    """
    yield None


class TestResolveRequestIdsFromFilters:
    """Test the resolve_request_ids_from_filters utility function"""

    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
    )
    def test_explicit_request_ids(self, mock_filter_queryset, db):
        """Test that explicit request_ids are returned directly without querying"""
        request_ids = ["req-1", "req-2", "req-3"]
        selection = PrivacyRequestBulkSelection(request_ids=request_ids)

        result = resolve_request_ids_from_filters(db, selection)

        assert result == request_ids
        # Should not call the filter function when request_ids is provided
        mock_filter_queryset.assert_not_called()

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
    )
    def test_filters_with_status(self, mock_filter_queryset, mock_privacy_request, db):
        """Test that filters are passed to filter_privacy_request_queryset correctly"""
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

        result = resolve_request_ids_from_filters(db, selection)

        # Verify the filter function was called with correct parameters
        mock_filter_queryset.assert_called_once()
        call_kwargs = mock_filter_queryset.call_args[1]
        assert call_kwargs["filters"].status == [PrivacyRequestStatus.pending]

        # Verify results
        assert result == ["pri_123", "pri_456"]

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
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

        result = resolve_request_ids_from_filters(db, selection)

        # Verify all filter parameters were passed via the filters object
        call_kwargs = mock_filter_queryset.call_args[1]
        passed_filters = call_kwargs["filters"]
        assert passed_filters.status == [
            PrivacyRequestStatus.pending,
            PrivacyRequestStatus.approved,
        ]
        assert passed_filters.external_id == "ext-123"
        assert passed_filters.location == "US"
        assert passed_filters.action_type == ActionType.access
        assert passed_filters.created_gt == now

        assert result == ["pri_789"]

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
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

        result = resolve_request_ids_from_filters(db, selection)

        # Verify that filter was called to exclude IDs
        mock_filter_query.filter.assert_called_once()

        # Results should not include excluded ID
        assert result == ["pri_222", "pri_333"]
        assert "pri_111" not in result

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
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

        result = resolve_request_ids_from_filters(db, selection)

        # Verify filter was called for exclusions
        mock_filter_query.filter.assert_called_once()

        # Results should have 3 items, excluding the two IDs
        assert len(result) == 3
        assert result == ["pri_333", "pri_444", "pri_555"]

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
    )
    def test_filters_no_results_returns_empty_list(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that an empty list is returned when filters return no results"""
        # Mock the query chain to return empty results
        mock_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_filter_queryset.return_value = mock_query

        # Return empty list
        mock_query.with_entities.return_value.all.return_value = []

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.canceled)
        )

        result = resolve_request_ids_from_filters(db, selection)

        assert result == []

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
    )
    def test_filters_all_excluded_returns_empty_list(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that an empty list is returned when all matching results are excluded"""
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

        result = resolve_request_ids_from_filters(db, selection)

        assert result == []

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
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

        resolve_request_ids_from_filters(db, selection)

        # Verify query_without_large_columns was called with db
        mock_privacy_request.query_without_large_columns.assert_called_once_with(db)

    @patch("fides.service.privacy_request.privacy_request_query_utils.PrivacyRequest")
    @patch(
        "fides.service.privacy_request.privacy_request_query_utils.filter_privacy_request_queryset"
    )
    def test_filters_max_results(
        self, mock_filter_queryset, mock_privacy_request, db
    ):
        """Test that a ValueError is raised when filter results exceed MAX_BULK_FILTER_RESULTS"""
        # Mock the query chain
        mock_query = MagicMock()
        mock_privacy_request.query_without_large_columns.return_value = mock_query
        mock_filter_queryset.return_value = mock_query

        # Return more results than the maximum allowed
        too_many_results = [(f"pri_{i}",) for i in range(MAX_BULK_FILTER_RESULTS + 1)]
        mock_query.with_entities.return_value.all.return_value = too_many_results

        selection = PrivacyRequestBulkSelection(
            filters=PrivacyRequestFilter(status=PrivacyRequestStatus.pending)
        )

        with pytest.raises(ValueError) as exc_info:
            resolve_request_ids_from_filters(db, selection)

        assert "exceeds the maximum" in str(exc_info.value)
        assert str(MAX_BULK_FILTER_RESULTS) in str(exc_info.value)

        # Test that exactly MAX_BULK_FILTER_RESULTS is allowed
        max_results = [(f"pri_{i}",) for i in range(MAX_BULK_FILTER_RESULTS)]
        mock_query.with_entities.return_value.all.return_value = max_results

        result = resolve_request_ids_from_filters(db, selection)
        assert result == [f"pri_{i}" for i in range(MAX_BULK_FILTER_RESULTS)]
