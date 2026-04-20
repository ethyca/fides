"""Tests for filtering privacy requests by duplicate_request_group_id."""

from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.duplicate_group import DuplicateGroup
from fides.common.scope_registry import PRIVACY_REQUEST_READ
from fides.common.urn_registry import (
    PRIVACY_REQUEST_SEARCH,
    V1_URL_PREFIX,
)


class TestPrivacyRequestDuplicateGroupFiltering:
    """Test filtering privacy requests by duplicate_request_group_id."""

    @pytest.fixture(scope="function")
    def duplicate_group(self, db):
        group = DuplicateGroup.create(
            db=db,
            data={"rule_version": "test-rule", "dedup_key": "test-dedup-key"},
        )
        yield group
        db.delete(group)
        db.commit()

    @pytest.fixture(scope="function")
    def other_duplicate_group(self, db):
        group = DuplicateGroup.create(
            db=db,
            data={"rule_version": "test-rule", "dedup_key": "other-dedup-key"},
        )
        yield group
        db.delete(group)
        db.commit()

    @pytest.fixture(scope="function")
    def privacy_requests_with_duplicate_group(
        self, db, policy, duplicate_group, other_duplicate_group
    ):
        """Create privacy requests assigned to two different duplicate groups plus an unassigned one."""
        requests = []

        for _ in range(2):
            pr = PrivacyRequest.create(
                db=db,
                data={
                    "policy_id": policy.id,
                    "status": "pending",
                    "duplicate_request_group_id": duplicate_group.id,
                },
            )
            requests.append(pr)

        pr_other = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "status": "pending",
                "duplicate_request_group_id": other_duplicate_group.id,
            },
        )
        requests.append(pr_other)

        pr_no_group = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "status": "pending",
            },
        )
        requests.append(pr_no_group)

        yield {
            "group": duplicate_group,
            "other_group": other_duplicate_group,
            "group_members": requests[:2],
            "other_group_member": requests[2],
            "unassigned": requests[3],
            "all": requests,
        }

        for request in requests:
            request.delete(db=db)

    def test_search_filter_by_duplicate_request_group_id_returns_group_members(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_duplicate_group,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        group_id = str(privacy_requests_with_duplicate_group["group"].id)
        response = api_client.post(
            url,
            json={"duplicate_request_group_id": group_id},
            headers=auth_header,
        )
        assert response.status_code == 200

        resp = response.json()
        expected_ids = {pr.id for pr in privacy_requests_with_duplicate_group["group_members"]}
        returned_ids = {item["id"] for item in resp["items"]}
        assert returned_ids == expected_ids
        for item in resp["items"]:
            assert item["duplicate_request_group_id"] == group_id

    def test_search_filter_by_nonexistent_duplicate_group_returns_empty(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_duplicate_group,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        response = api_client.post(
            url,
            json={"duplicate_request_group_id": str(uuid4())},
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_search_filter_by_other_group_excludes_unrelated_requests(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_duplicate_group,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        other_group_id = str(privacy_requests_with_duplicate_group["other_group"].id)
        response = api_client.post(
            url,
            json={"duplicate_request_group_id": other_group_id},
            headers=auth_header,
        )
        assert response.status_code == 200

        resp = response.json()
        assert len(resp["items"]) == 1
        assert (
            resp["items"][0]["id"]
            == privacy_requests_with_duplicate_group["other_group_member"].id
        )

    def test_search_filter_invalid_uuid_returns_422(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests_with_duplicate_group,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        response = api_client.post(
            url,
            json={"duplicate_request_group_id": "not-a-uuid"},
            headers=auth_header,
        )
        assert response.status_code == 422
