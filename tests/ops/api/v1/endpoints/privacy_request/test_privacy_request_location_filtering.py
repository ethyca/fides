"""Tests for privacy request location filtering functionality."""

import pytest
from starlette.testclient import TestClient

from fides.api.models.privacy_request import PrivacyRequest
from fides.common.api.scope_registry import PRIVACY_REQUEST_READ
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_SEARCH,
    PRIVACY_REQUESTS,
    V1_URL_PREFIX,
)


class TestPrivacyRequestLocationFiltering:
    """Test location-based filtering for privacy requests."""

    @pytest.fixture(scope="function")
    def privacy_requests_with_locations(self, db, policy):
        """Create privacy requests with different locations for testing."""
        requests = []

        # US country only
        pr_us = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": "US",
                "status": "pending",
            },
        )
        requests.append(pr_us)

        # US subdivision
        pr_us_ca = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": "US-CA",
                "status": "pending",
            },
        )
        requests.append(pr_us_ca)

        # Different US subdivision
        pr_us_ny = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": "US-NY",
                "status": "pending",
            },
        )
        requests.append(pr_us_ny)

        # Different country
        pr_gb = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": "GB",
                "status": "pending",
            },
        )
        requests.append(pr_gb)

        # Canada with subdivision
        pr_ca_on = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": "CA-ON",
                "status": "pending",
            },
        )
        requests.append(pr_ca_on)

        # Special EEA code
        pr_eea = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": "EEA",
                "status": "pending",
            },
        )
        requests.append(pr_eea)

        # No location
        pr_no_location = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "location": None,
                "status": "pending",
            },
        )
        requests.append(pr_no_location)

        yield requests

        # Clean up
        for request in requests:
            request.delete(db=db)

    def test_get_privacy_requests_filter_by_country_code(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test filtering by country code matches both country and subdivisions."""
        url = V1_URL_PREFIX + PRIVACY_REQUESTS
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Filter by US - should match "US", "US-CA", and "US-NY"
        response = api_client.get(url + "?location=US", headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 3

        locations = sorted([item["location"] for item in resp["items"]])
        assert locations == ["US", "US-CA", "US-NY"]

    def test_get_privacy_requests_filter_by_subdivision_code(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test filtering by subdivision code matches only exact subdivision."""
        url = V1_URL_PREFIX + PRIVACY_REQUESTS
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Filter by US-CA - should match only "US-CA"
        response = api_client.get(url + "?location=US-CA", headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["location"] == "US-CA"

    def test_get_privacy_requests_filter_by_special_codes(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test filtering by special codes like EEA."""
        url = V1_URL_PREFIX + PRIVACY_REQUESTS
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Filter by EEA
        response = api_client.get(url + "?location=EEA", headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["location"] == "EEA"

    def test_get_privacy_requests_filter_by_nonexistent_location(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test filtering by non-existent location returns empty results."""
        url = V1_URL_PREFIX + PRIVACY_REQUESTS
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Filter by non-existent location
        response = api_client.get(url + "?location=ZZ", headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 0

    def test_privacy_request_search_filter_by_location(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test location filtering using the POST search endpoint."""
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Filter by CA (Canada) - should match "CA-ON" only
        filter_data = {"location": "CA"}
        response = api_client.post(url, json=filter_data, headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["location"] == "CA-ON"

    def test_privacy_request_search_no_location_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test that requests without location filter return all requests."""
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # No location filter - should return all requests
        filter_data = {}
        response = api_client.post(url, json=filter_data, headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        # Should return all 7 requests (US, US-CA, US-NY, GB, CA-ON, EEA, None)
        assert len(resp["items"]) == 7

    def test_case_insensitive_location_filtering(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_locations,
    ):
        """Test that location filtering is case insensitive."""
        url = V1_URL_PREFIX + PRIVACY_REQUESTS
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Test lowercase input
        response = api_client.get(url + "?location=us", headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 3  # US, US-CA, US-NY

        # Test mixed case input
        response = api_client.get(url + "?location=Us-Ca", headers=auth_header)
        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["location"] == "US-CA"
