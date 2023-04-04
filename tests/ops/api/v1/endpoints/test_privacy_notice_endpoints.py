from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

import pytest
from fideslang import DataUse
from starlette.exceptions import HTTPException
from starlette.testclient import TestClient

from fides.api.ctl.sql_models import DataUse as sql_DataUse
from fides.api.ops.api.v1 import scope_registry as scopes
from fides.api.ops.api.v1.endpoints.privacy_notice_endpoints import (
    validate_notice_data_uses,
)
from fides.api.ops.api.v1.urn_registry import (
    PRIVACY_NOTICE,
    PRIVACY_NOTICE_DETAIL,
    V1_URL_PREFIX,
)
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeHistory,
    PrivacyNoticeRegion,
)
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeCreation


class TestValidateDataUses:
    @pytest.fixture(scope="function")
    def privacy_notice_request(self):
        return PrivacyNoticeCreation(
            name="sample privacy notice",
            regions=[PrivacyNoticeRegion.us_ca],
            consent_mechanism=ConsentMechanism.opt_in,
            data_uses=["placeholder"],
            enforcement_level=EnforcementLevel.system_wide,
        )

    @pytest.fixture(scope="function")
    def custom_data_use(self, db):
        return sql_DataUse.create(
            db=db,
            data=DataUse(
                fides_key="new_data_use",
                organization_fides_key="default_organization",
                name="New data use",
                description="A test data use",
                parent_key=None,
                is_default=True,
            ).dict(),
        )

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_invalid(
        self, db, privacy_notice_request: PrivacyNoticeCreation
    ):
        privacy_notice_request.data_uses = ["invalid_data_use"]
        with pytest.raises(HTTPException):
            validate_notice_data_uses([privacy_notice_request], db)

        privacy_notice_request.data_uses = ["advertising", "invalid_data_use"]
        with pytest.raises(HTTPException):
            validate_notice_data_uses([privacy_notice_request], db)

        privacy_notice_request.data_uses = [
            "advertising",
            "advertising.invalid_data_use",
        ]
        with pytest.raises(HTTPException):
            validate_notice_data_uses([privacy_notice_request], db)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_default_taxonomy(
        self, db, privacy_notice_request: PrivacyNoticeCreation
    ):
        privacy_notice_request.data_uses = ["advertising"]
        validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["advertising", "provide"]
        validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["advertising", "provide", "provide.service"]
        validate_notice_data_uses([privacy_notice_request], db)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_custom_uses(
        self,
        db,
        privacy_notice_request: PrivacyNoticeCreation,
        custom_data_use: sql_DataUse,
    ):
        """
        Ensure custom data uses added to the DB are considered valid
        """

        privacy_notice_request.data_uses = [custom_data_use.fides_key]
        validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["advertising", custom_data_use.fides_key]
        validate_notice_data_uses([privacy_notice_request], db)


class TestGetPrivacyNotices:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_NOTICE

    def test_get_privacy_notices_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_privacy_notices_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.usefixtures(
        "privacy_notice",
        "privacy_notice_us_co_third_party_sharing",
        "system",
    )
    def test_get_privacy_notices_defaults(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_notice_us_ca_provide: PrivacyNotice,
        db,
    ):
        # we should have 3 privacy notices in the db
        assert len(PrivacyNotice.all(db)) == 3

        # update this privacy notice to associate it with a data use associatd with a system
        # this allows us to get > 1 object in our response to the API call
        privacy_notice_us_ca_provide.update(
            db, data={"data_uses": ["advertising", "provide"]}
        )

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert all 3 notices are in the response
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # now we just assert the expected fields are on each response item
        for notice_detail in data["items"]:
            assert "id" in notice_detail
            assert "created_at" in notice_detail
            assert "updated_at" in notice_detail
            assert "name" in notice_detail
            assert "description" in notice_detail
            assert "regions" in notice_detail
            assert "consent_mechanism" in notice_detail
            assert "data_uses" in notice_detail
            assert "version" in notice_detail
            assert "disabled" in notice_detail
            assert "has_gpc_flag" in notice_detail
            assert "displayed_in_privacy_center" in notice_detail
            assert "displayed_in_privacy_modal" in notice_detail
            assert "displayed_in_banner" in notice_detail
            assert "enforcement_level" in notice_detail

    @pytest.mark.usefixtures(
        "privacy_notice",
        "privacy_notice_us_ca_provide",
        "privacy_notice_us_co_third_party_sharing",
        "system",
    )
    def test_get_privacy_notices_systems_applicable_false(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db,
    ):
        # we should have 3 privacy notices in the db
        assert len(PrivacyNotice.all(db)) == 3

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])

        # first test the "base case", where systems_applicable should default to true
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        # assert all 3 notices are in response since we're not filtering
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # now test that setting the param to true works
        resp = api_client.get(
            url + "?systems_applicable=true",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert only 1 notice is in response since we're filtering for systems_applicable=true
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # now test that disabling the filter works the same as the default
        resp = api_client.get(
            url + "?systems_applicable=false",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert all 3 notices are in response since we're not filtering by systems_applicable
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # and just sanity check the expected fields are on each response item
        for notice_detail in data["items"]:
            assert "id" in notice_detail
            assert "created_at" in notice_detail
            assert "updated_at" in notice_detail
            assert "name" in notice_detail
            assert "description" in notice_detail
            assert "regions" in notice_detail
            assert "consent_mechanism" in notice_detail
            assert "data_uses" in notice_detail
            assert "version" in notice_detail
            assert "disabled" in notice_detail
            assert "has_gpc_flag" in notice_detail
            assert "displayed_in_privacy_center" in notice_detail
            assert "displayed_in_privacy_modal" in notice_detail
            assert "displayed_in_banner" in notice_detail
            assert "enforcement_level" in notice_detail

    @pytest.mark.usefixtures(
        "privacy_notice_us_co_third_party_sharing",
        "system",
    )
    def test_get_privacy_notices_region_filtered(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_notice: PrivacyNotice,
        url,
        db,
    ):
        # we should have 2 privacy notices in the db
        assert len(PrivacyNotice.all(db)) == 2

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])

        # first test the base case, i.e. no filtering gives us back the two notices
        resp = api_client.get(
            url + "?systems_applicable=false",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        # assert the 2 notices are in the response since no filter was specified
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # now test that the filter/param works as expected
        resp = api_client.get(
            url + "?systems_applicable=false&region=us_ca",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        # assert only one notice in response since only one matches our region filter
        assert data["total"] == 1
        assert len(data["items"]) == 1

        # now we just assert it's the correct privacy notice in the response
        privacy_notice_response_data = data["items"][0]
        assert privacy_notice_response_data["id"] == privacy_notice.id
        assert privacy_notice_response_data["name"] == privacy_notice.name
        for region in privacy_notice_response_data["regions"]:
            assert PrivacyNoticeRegion(region) in privacy_notice.regions
        for data_use in privacy_notice_response_data["data_uses"]:
            assert data_use in privacy_notice.data_uses

    @pytest.mark.usefixtures(
        "privacy_notice_us_ca_provide",
        "privacy_notice_us_co_third_party_sharing",
        "system",
    )
    def test_get_privacy_notices_show_disabled_false(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_notice: PrivacyNotice,
        db,
    ):
        # make one of our 3 privacy notices disabled=true
        privacy_notice.update(db, data={"disabled": True})
        # we should still have 3 privacy notices in the db
        assert len(PrivacyNotice.all(db)) == 3

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])

        # first we ensure our "base" request does not filter out the disabled notice
        resp = api_client.get(
            url + "?systems_applicable=false",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        # assert all 3 notices are still in response since we haven't filtered disabled
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # next we ensure show_disabled=true does not filter out the disabled notice
        resp = api_client.get(
            url + "?systems_applicable=false&show_disabled=true",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        # assert all 3 notices are still in response since we haven't filtered disabled
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # now we test that show_disabled=false filters out the disabled notice
        resp = api_client.get(
            url + "?systems_applicable=false&show_disabled=false",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert only 1 notice is in response since we're filtering out disabled now
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.usefixtures(
        "system",
    )
    def test_pagination_ordering(
        self,
        db,
        oauth_client,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        privacy_notices = []
        PRIVACY_NOTICE_COUNT = 50
        for _ in range(PRIVACY_NOTICE_COUNT):
            name = str(uuid4())
            privacy_notices.append(
                PrivacyNotice.create(
                    db=db,
                    data={
                        "name": name,
                        "description": "a sample privacy notice configuration",
                        "regions": [PrivacyNoticeRegion.us_ca],
                        "consent_mechanism": ConsentMechanism.opt_in,
                        "data_uses": ["advertising"],
                        "enforcement_level": EnforcementLevel.system_wide,
                    },
                )
            )

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        assert data["total"] == PRIVACY_NOTICE_COUNT

        for privacy_notice in data["items"]:
            # The most recent privacy_notice will be that which was last added to `privacy_notices`
            most_recent = privacy_notices.pop()
            assert privacy_notice["name"] == most_recent.name

    @pytest.mark.usefixtures(
        "system",
    )
    def test_pagination(
        self,
        db,
        oauth_client,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        privacy_notices = []
        PRIVACY_NOTICE_COUNT = 75
        for _ in range(PRIVACY_NOTICE_COUNT):
            name = str(uuid4())
            privacy_notices.append(
                PrivacyNotice.create(
                    db=db,
                    data={
                        "name": name,
                        "description": "a sample privacy notice configuration",
                        "regions": [PrivacyNoticeRegion.us_ca],
                        "consent_mechanism": ConsentMechanism.opt_in,
                        "data_uses": ["advertising"],
                        "enforcement_level": EnforcementLevel.system_wide,
                    },
                )
            )

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        assert len(data["items"]) == 50
        assert data["total"] == PRIVACY_NOTICE_COUNT

        for privacy_notice in data["items"]:
            # The most recent privacy_notice will be that which was last added to `privacy_notices`
            most_recent = privacy_notices.pop()
            assert privacy_notice["name"] == most_recent.name

        resp_page_2 = api_client.get(
            url + "?page=2",
            headers=auth_header,
        )

        assert resp_page_2.status_code == 200
        data_page_2 = resp_page_2.json()

        assert "items" in data_page_2
        assert len(data_page_2["items"]) == PRIVACY_NOTICE_COUNT - 50
        assert data_page_2["total"] == PRIVACY_NOTICE_COUNT

        for privacy_notice in data_page_2["items"]:
            # The most recent privacy_notice will be last added to `privacy_notices` that still remains
            most_recent = privacy_notices.pop()
            assert privacy_notice["name"] == most_recent.name


class TestGetPrivacyNoticeDetail:
    @pytest.fixture(scope="function")
    def url(self, privacy_notice) -> str:
        return V1_URL_PREFIX + PRIVACY_NOTICE_DETAIL.format(
            privacy_notice_id=privacy_notice.id
        )

    def test_get_privacy_notice_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_privacy_notice_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_invalid_privacy_notice(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        url = V1_URL_PREFIX + PRIVACY_NOTICE_DETAIL.format(privacy_notice_id="bad")

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 404

    def test_get_privacy_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_notice: PrivacyNotice,
        url,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == privacy_notice.id
        assert data["name"] == privacy_notice.name
        assert data["description"] == privacy_notice.description
        assert data["origin"] == privacy_notice.origin
        assert data["created_at"] == privacy_notice.created_at.isoformat()
        assert data["updated_at"] == privacy_notice.updated_at.isoformat()
        for region in data["regions"]:
            assert PrivacyNoticeRegion(region) in privacy_notice.regions
        for data_use in data["data_uses"]:
            assert data_use in privacy_notice.data_uses
        assert (
            ConsentMechanism(data["consent_mechanism"])
            == privacy_notice.consent_mechanism
        )
        assert (
            EnforcementLevel(data["enforcement_level"])
            == privacy_notice.enforcement_level
        )
        assert data["version"] == privacy_notice.version
        assert data["disabled"] == privacy_notice.disabled
        assert data["displayed_in_banner"] == privacy_notice.displayed_in_banner


class TestPostPrivacyNotices:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_NOTICE

    @pytest.fixture(scope="function")
    def notice_request(self, load_default_data_uses) -> Dict[str, Any]:
        return {
            "name": "test privacy notice 1",
            "description": "my test privacy notice",
            "origin": "privacy_notice_template_1",
            "regions": [PrivacyNoticeRegion.eu_be.value, PrivacyNoticeRegion.us_ca.value],
            "consent_mechanism": ConsentMechanism.opt_in.value,
            "data_uses": ["advertising"],
            "enforcement_level": EnforcementLevel.system_wide.value,
        }

    @pytest.fixture(scope="function")
    def notice_request_2(self, load_default_data_uses) -> Dict[str, Any]:
        return {
            "name": "test privacy notice 2",
            # no description or origin on this request just to verify their optionality
            "regions": [PrivacyNoticeRegion.us_ca.value],
            "consent_mechanism": ConsentMechanism.opt_in.value,
            "data_uses": ["personalize"],
            "enforcement_level": EnforcementLevel.system_wide.value,
        }

    def test_post_privacy_notice_unauthenticated(self, url, api_client):
        resp = api_client.post(url)
        assert resp.status_code == 401

    def test_post_privacy_notice_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        resp = api_client.post(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_post_invalid_privacy_notice_missing_field(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        notice_request: dict[str, Any],
        notice_request_2: dict[str, Any],
    ):
        """
        Test posting privacy notice(s) with a missing field is rejected
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])
        notice_request_no_name: dict[str, Any] = notice_request.copy()
        notice_request_no_name.pop("name")
        # try post with invalid request structure, i.e. missing field
        resp = api_client.post(url, headers=auth_header, json=[notice_request_no_name])
        assert resp.status_code == 422

        # try post with 2 notices, one with invalid request structure, i.e. missing field
        resp = api_client.post(
            url,
            headers=auth_header,
            json=[notice_request_no_name, notice_request_2],
        )
        assert resp.status_code == 422

    def test_post_invalid_privacy_notice_includes_id(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        notice_request: dict[str, Any],
        notice_request_2: dict[str, Any],
    ):
        """
        Test posting privacy notice(s) with an ID field is rejected
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])
        notice_request_with_id: dict[str, Any] = notice_request.copy()
        notice_request_with_id["id"] = "pn_1"

        resp = api_client.post(url, headers=auth_header, json=[notice_request_with_id])
        assert resp.status_code == 422

    def test_post_invalid_privacy_notice_invalid_values(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        notice_request: dict[str, Any],
    ):
        """
        Test posting privacy notice(s) with various invalid enum values is rejected
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])

        ### regions field ###

        notice_request_bad_region: dict[str, Any] = notice_request.copy()
        # try post with empty regions list specified, should be rejected
        notice_request_bad_region["regions"] = []
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_region]
        )
        assert resp.status_code == 422

        notice_request_bad_region["regions"] = ["invalid_region"]
        # try post with invalid region specified, should be rejected
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_region]
        )
        assert resp.status_code == 422

        notice_request_bad_region["regions"] = [
            PrivacyNoticeRegion.eu_be.value,
            "invalid_region",
        ]
        # try post with one invalid region one valid region specified, should be rejected
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_region]
        )
        assert resp.status_code == 422

        notice_request_bad_region.pop("regions")
        # try post with no regions key, should be rejected
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_region]
        )
        assert resp.status_code == 422

        ### data_uses field ###

        notice_request_bad_data_uses: dict[str, Any] = notice_request.copy()

        # try post with empty data_uses list specified, should be rejected
        notice_request_bad_data_uses["data_uses"] = []
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_data_uses]
        )
        assert resp.status_code == 422

        notice_request_bad_data_uses["data_uses"] = ["invalid_data_use"]
        # try post with invalid data_use specified, should be rejected
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_data_uses]
        )
        assert resp.status_code == 422

        notice_request_bad_data_uses["data_uses"] = ["advertising", "invalid_data_use"]
        # try post with one invalid data_use one valid data_use specified, should be rejected
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_data_uses]
        )
        assert resp.status_code == 422

        notice_request_bad_data_uses.pop("data_uses")
        # try post with no data_uses key, should be rejected
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_bad_data_uses]
        )
        assert resp.status_code == 422

        ### consent_mechanism field ###

        notice_request_bad_cm: dict[str, Any] = notice_request.copy()

        notice_request_bad_cm["consent_mechanism"] = ["invalid_mechanism"]
        # try post with invalid consent_mechanism specified, should be rejected
        resp = api_client.post(url, headers=auth_header, json=[notice_request_bad_cm])
        assert resp.status_code == 422

        ### enforcement_level field ###

        notice_request_bad_el: dict[str, Any] = notice_request.copy()

        notice_request_bad_el["enforcement_level"] = ["invalid"]
        # try post with invalid enforcement_level specified, should be rejected
        resp = api_client.post(url, headers=auth_header, json=[notice_request_bad_el])
        assert resp.status_code == 422

    def test_post_invalid_privacy_notice_data_use_conflicts_within_request(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        notice_request: dict[str, Any],
    ):
        """
        Test posting privacy notice(s) with data_use conflicts
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])

        # conflict with identical data uses within region
        notice_request_identical_use = notice_request.copy()
        # change the name on the copied notice so that it's "different"
        notice_request_identical_use["name"] = "different notice name"
        # keep one overlapping region with other request notice, no overlaps with
        notice_request_identical_use["regions"] = [PrivacyNoticeRegion.eu_be.value]
        resp = api_client.post(
            url,
            headers=auth_header,
            json=[notice_request, notice_request_identical_use],
        )  # overlap of eu and "advertising" data_use
        assert resp.status_code == 422

        # conflict with parent/child data uses within region
        notice_request_child_use = notice_request.copy()
        # change the name on the copied notice so that it's "different"
        notice_request_child_use["name"] = "different notice name"
        # keep one overlapping region with other request notice, no overlaps with
        notice_request_child_use["region"] = [PrivacyNoticeRegion.eu_be.value]
        # update our data_use to be a child of the other request notice
        notice_request_child_use["data_use"] = ["advertising.first_party"]

        resp = api_client.post(
            url, headers=auth_header, json=[notice_request, notice_request_child_use]
        )  # overlap of eu and "advertising" data_use as a parent
        assert resp.status_code == 422

    def test_post_invalid_privacy_notice_data_use_conflicts_with_existing_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_notice: PrivacyNotice,
        privacy_notice_us_co_third_party_sharing: PrivacyNotice,
        notice_request: dict[str, Any],
        db,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])

        # conflict with identical data uses within region
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request]
        )  # overlap of us_ca and "advertising" data_use
        assert resp.status_code == 422

        # conflict with parent/child data uses within region
        notice_request_updated_data_use = notice_request.copy()
        notice_request_updated_data_use["data_uses"] = [
            "advertising.first_party",
            "third_party_sharing",
        ]

        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_updated_data_use]
        )
        assert resp.status_code == 422

        # disable our privacy notice causing the conflict
        privacy_notice.update(db, data={"disabled": True})
        # and ensure things work as expected since we've disabled our privacy notice
        resp = api_client.post(
            url, headers=auth_header, json=[notice_request_updated_data_use]
        )
        assert resp.status_code == 200

    def test_post_privacy_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        notice_request: dict[str, Any],
        url,
        db,
    ):
        """
        Test posting a single new privacy notice
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])

        before_creation = datetime.now().isoformat()

        resp = api_client.post(url, headers=auth_header, json=[notice_request])
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        response_notice = resp.json()[0]

        assert response_notice["name"] == notice_request["name"]
        assert "id" in response_notice
        assert response_notice["version"] == 1.0
        assert response_notice["created_at"] < datetime.now().isoformat()
        assert response_notice["created_at"] > before_creation
        assert response_notice["updated_at"] < datetime.now().isoformat()
        assert response_notice["updated_at"] > before_creation
        assert not response_notice["disabled"]

        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        assert response_notice["name"] == db_notice.name
        assert response_notice["version"] == db_notice.version
        assert response_notice["created_at"] == db_notice.created_at.isoformat()
        assert response_notice["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice["disabled"] == db_notice.disabled

    def test_post_privacy_notice_twice_same_name(
        self,
        api_client: TestClient,
        generate_auth_header,
        notice_request: dict[str, Any],
        url,
        db,
    ):
        """
        Test posting two valid privacy notices with the same name works well to create
        two distinct db records
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])

        # our first request just like above
        before_creation = datetime.now().isoformat()

        resp = api_client.post(url, headers=auth_header, json=[notice_request])
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        response_notice = resp.json()[0]

        assert response_notice["name"] == notice_request["name"]
        assert "id" in response_notice
        assert response_notice["version"] == 1.0
        assert response_notice["created_at"] < datetime.now().isoformat()
        assert response_notice["created_at"] > before_creation
        assert response_notice["updated_at"] < datetime.now().isoformat()
        assert response_notice["updated_at"] > before_creation
        assert not response_notice["disabled"]

        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        assert response_notice["name"] == db_notice.name
        assert response_notice["version"] == db_notice.version
        assert response_notice["created_at"] == db_notice.created_at.isoformat()
        assert response_notice["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice["disabled"] == db_notice.disabled

        # now for our second request

        # change the region here to avoid data use validation errors
        notice_request["regions"] = [PrivacyNoticeRegion.us_co.value]
        before_creation_2 = datetime.now().isoformat()
        resp_2 = api_client.post(url, headers=auth_header, json=[notice_request])
        assert resp_2.status_code == 200
        assert len(resp_2.json()) == 1
        response_notice_2 = resp_2.json()[0]

        assert response_notice_2["name"] == notice_request["name"]
        assert "id" in response_notice_2
        assert response_notice_2["version"] == 1.0
        assert response_notice_2["created_at"] < datetime.now().isoformat()
        assert response_notice_2["created_at"] > before_creation_2
        assert response_notice_2["updated_at"] < datetime.now().isoformat()
        assert response_notice_2["updated_at"] > before_creation_2
        assert not response_notice_2["disabled"]

        db_notice_2: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice_2["id"]
        )
        db.refresh(db_notice_2)
        assert response_notice_2["name"] == db_notice_2.name
        assert response_notice_2["version"] == db_notice_2.version
        assert response_notice_2["created_at"] == db_notice_2.created_at.isoformat()
        assert response_notice_2["updated_at"] == db_notice_2.updated_at.isoformat()
        assert response_notice_2["disabled"] == db_notice_2.disabled

        # and now just assert the two notices are actually distinct records
        assert db_notice.id != db_notice_2.id

    def test_post_multiple_privacy_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        notice_request: dict[str, Any],
        notice_request_2: dict[str, Any],
        url,
        db,
    ):
        """
        Test posting multiple new privacy notices
        """

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_CREATE])

        before_creation = datetime.now().isoformat()

        resp = api_client.post(
            url, headers=auth_header, json=[notice_request, notice_request_2]
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # first response is first request object
        response_notice = resp.json()[0]
        assert response_notice["name"] == notice_request["name"]
        assert "id" in response_notice
        assert response_notice["version"] == 1.0
        assert response_notice["created_at"] < datetime.now().isoformat()
        assert response_notice["created_at"] > before_creation
        assert response_notice["updated_at"] < datetime.now().isoformat()
        assert response_notice["updated_at"] > before_creation
        assert not response_notice["disabled"]

        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        assert response_notice["name"] == db_notice.name
        assert response_notice["version"] == db_notice.version
        assert response_notice["created_at"] == db_notice.created_at.isoformat()
        assert response_notice["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice["disabled"] == db_notice.disabled

        # second response is first request object
        response_notice_2 = resp.json()[1]
        assert response_notice_2["name"] == notice_request_2["name"]
        assert "id" in response_notice_2
        assert response_notice_2["version"] == 1.0
        assert response_notice_2["created_at"] < datetime.now().isoformat()
        assert response_notice_2["created_at"] > before_creation
        assert response_notice_2["updated_at"] < datetime.now().isoformat()
        assert response_notice_2["updated_at"] > before_creation
        assert not response_notice_2["disabled"]

        db_notice_2: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice_2["id"]
        )
        db.refresh(db_notice_2)
        assert response_notice_2["name"] == db_notice_2.name
        assert response_notice_2["version"] == db_notice_2.version
        assert response_notice_2["created_at"] == db_notice_2.created_at.isoformat()
        assert response_notice_2["updated_at"] == db_notice_2.updated_at.isoformat()
        assert response_notice_2["disabled"] == db_notice_2.disabled


class TestPatchPrivacyNotices:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_NOTICE

    @pytest.fixture(scope="function")
    def patch_privacy_notice_payload(
        self, privacy_notice: PrivacyNotice, load_default_data_uses
    ):
        return {
            "id": privacy_notice.id,
            "name": "updated privacy notice name",
            "disabled": True,
            "regions": [
                PrivacyNoticeRegion.us_ca.value,
            ],
            "consent_mechanism": ConsentMechanism.opt_out.value,
            "data_uses": ["advertising"],
        }

    @pytest.fixture(scope="function")
    def patch_privacy_notice_payload_us_ca_provide(
        self, privacy_notice_us_ca_provide: PrivacyNotice, load_default_data_uses
    ):
        return {
            "id": privacy_notice_us_ca_provide.id,
            "description": "updated description",
        }

    def test_patch_privacy_notice_unauthenticated(self, url, api_client):
        resp = api_client.patch(url)
        assert resp.status_code == 401

    def test_patch_privacy_notice_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        resp = api_client.patch(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_patch_duplicate_privacy_notices_throws_error(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        patch_privacy_notice_payload: dict[str, Any],
        privacy_notice: PrivacyNotice,
        db,
    ):
        """
        Test that attempting a PATCH with multiple privacy requests with the same ID
        throws a 422
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        # just create a slightly altered privacy request entity, keep the ID the same
        patch_request_cloned: dict[str, Any] = patch_privacy_notice_payload.copy()
        patch_request_cloned["name"] = "a different name udpate"
        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[patch_privacy_notice_payload, patch_request_cloned],
        )
        assert resp.status_code == 422

    def test_patch_invalid_privacy_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        patch_privacy_notice_payload: dict[str, Any],
        privacy_notice: PrivacyNotice,
        db,
    ):
        """
        Test patch privacy notice(s) with missing or invalid id field
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        # test with no ID provided
        patch_request_no_id: dict[str, Any] = patch_privacy_notice_payload.copy()
        patch_request_no_id.pop("id")
        resp = api_client.patch(url, headers=auth_header, json=[patch_request_no_id])
        assert resp.status_code == 422
        # assert db record hasn't been updated
        assert (
            privacy_notice.name
            == PrivacyNotice.get(db=db, object_id=privacy_notice.id).name
        )

        # and ensure even if one item with no ID is passed, whole request is rejected
        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[patch_request_no_id, patch_privacy_notice_payload],
        )
        assert resp.status_code == 422
        # assert db record hasn't been updated
        assert (
            privacy_notice.name
            == PrivacyNotice.get(db=db, object_id=privacy_notice.id).name
        )

        # test with invalid ID
        patch_request_invalid_id: dict[str, Any] = patch_privacy_notice_payload.copy()
        patch_request_invalid_id["id"] = "invalid"
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_request_invalid_id]
        )
        assert resp.status_code == 404
        # assert db record hasn't been updated
        assert (
            privacy_notice.name
            == PrivacyNotice.get(db=db, object_id=privacy_notice.id).name
        )

        # and ensure even if one item with an invalid ID is passed, whole request is rejected
        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[patch_request_invalid_id, patch_privacy_notice_payload],
        )
        assert resp.status_code == 404
        # assert db record hasn't been updated
        assert (
            privacy_notice.name
            == PrivacyNotice.get(db=db, object_id=privacy_notice.id).name
        )

    def test_patch_privacy_notice_invalid_body(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        patch_privacy_notice_payload: dict[str, Any],
    ):
        """
        Test patching privacy notice(s) with various invalid bodies
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        ### regions field ###

        patch_privacy_notice_payload_bad_region: dict[
            str, Any
        ] = patch_privacy_notice_payload.copy()
        # try patch with empty regions list specified, should be rejected
        patch_privacy_notice_payload_bad_region["regions"] = []
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_region]
        )
        assert resp.status_code == 422

        patch_privacy_notice_payload_bad_region["regions"] = ["invalid_region"]
        # try patch with invalid region specified, should be rejected
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_region]
        )
        assert resp.status_code == 422

        patch_privacy_notice_payload_bad_region["regions"] = [
            PrivacyNoticeRegion.eu_be.value,
            "invalid_region",
        ]
        # try patch with one invalid region one valid region specified, should be rejected
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_region]
        )
        assert resp.status_code == 422

        ### data_uses field ###

        patch_privacy_notice_payload_bad_data_uses: dict[
            str, Any
        ] = patch_privacy_notice_payload.copy()

        # try patch with empty data_uses list specified, should be rejected
        patch_privacy_notice_payload_bad_data_uses["data_uses"] = []
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_data_uses]
        )
        assert resp.status_code == 422

        patch_privacy_notice_payload_bad_data_uses["data_uses"] = ["invalid_data_use"]
        # try patch with invalid data_use specified, should be rejected
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_data_uses]
        )
        assert resp.status_code == 422

        patch_privacy_notice_payload_bad_data_uses["data_uses"] = [
            "advertising",
            "invalid_data_use",
        ]
        # try patch with one invalid data_use one valid data_use specified, should be rejected
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_data_uses]
        )
        assert resp.status_code == 422

        ### consent_mechanism field ###

        patch_privacy_notice_payload_bad_cm: dict[
            str, Any
        ] = patch_privacy_notice_payload.copy()

        patch_privacy_notice_payload_bad_cm["consent_mechanism"] = ["invalid_mechanism"]
        # try patch with invalid consent_mechanism specified, should be rejected
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_cm]
        )
        assert resp.status_code == 422

        ### enforcement_level field ###

        patch_privacy_notice_payload_bad_el: dict[
            str, Any
        ] = patch_privacy_notice_payload.copy()

        patch_privacy_notice_payload_bad_el["enforcement_level"] = ["invalid"]
        # try patch with invalid enforcement_level specified, should be rejected
        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload_bad_el]
        )
        assert resp.status_code == 422

    def test_patch_invalid_privacy_notice_data_use_conflicts_within_request(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        patch_privacy_notice_payload: dict[str, Any],
        patch_privacy_notice_payload_us_ca_provide: dict[str, Any],
    ):
        """
        Test patching privacy notice(s) with data_use conflicts within the request payload
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        # conflict with identical data uses within region
        # we make the two patch payload items have the same data_use, they should fail
        patch_privacy_notice_payload_updated_data_use = (
            patch_privacy_notice_payload.copy()
        )
        patch_privacy_notice_payload_updated_data_use["data_uses"] = ["improve"]
        # ensure we are not disabling privacy notice, because that will bypass validation
        patch_privacy_notice_payload_updated_data_use["disabled"] = False

        patch_privacy_notice_us_ca_updated_data_use = (
            patch_privacy_notice_payload_us_ca_provide.copy()
        )
        patch_privacy_notice_us_ca_updated_data_use["data_uses"] = ["improve"]

        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload_updated_data_use,
                patch_privacy_notice_us_ca_updated_data_use,
            ],
        )  # direct overlap in the requests
        assert resp.status_code == 422

        # conflict with parent/child data uses within region
        # we make the two patch payload items have parent/child data uses, they should fail
        patch_privacy_notice_us_ca_updated_data_use["data_uses"] = ["improve.system"]

        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload_updated_data_use,
                patch_privacy_notice_us_ca_updated_data_use,
            ],
        )  # parent/child overlap in the requests
        assert resp.status_code == 422

    def test_patch_invalid_privacy_notice_data_use_conflicts_with_existing_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_notice: PrivacyNotice,
        privacy_notice_us_co_third_party_sharing: PrivacyNotice,
        patch_privacy_notice_payload: dict[str, Any],
        patch_privacy_notice_payload_us_ca_provide: dict[str, Any],
        db,
    ):
        """
        Test patching privacy notice(s) with data_use conflicts with existing privacy notices
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        patch_privacy_notice_us_ca_updated_data_use = (
            patch_privacy_notice_payload_us_ca_provide.copy()
        )
        # we make the patch payload conflict with the existing notice in the db
        patch_privacy_notice_us_ca_updated_data_use["data_uses"] = ["advertising"]

        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_us_ca_updated_data_use,
            ],
        )  # direct overlap with existing privacy notice
        assert resp.status_code == 422

        # we make the patch payload conflict with the existing notice in the db
        patch_privacy_notice_us_ca_updated_data_use["data_uses"] = [
            "advertising.first_party"
        ]

        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_us_ca_updated_data_use,
            ],
        )  # parent/child overlap with existing privacy notice
        assert resp.status_code == 422

        # but if we disable the conflicting privacy notice in the db, we should succeed
        privacy_notice.update(db, data={"disabled": True})
        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_us_ca_updated_data_use,
            ],
        )
        assert resp.status_code == 200

    def test_patch_invalid_privacy_notice_data_use_conflicts_enable_disable(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_notice: PrivacyNotice,
        privacy_notice_us_co_third_party_sharing: PrivacyNotice,
        patch_privacy_notice_payload: dict[str, Any],
        patch_privacy_notice_payload_us_ca_provide: dict[str, Any],
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        patch_privacy_notice_us_ca_updated_data_use = (
            patch_privacy_notice_payload_us_ca_provide.copy()
        )
        # we make the patch payload conflict with the existing notice in the db
        patch_privacy_notice_us_ca_updated_data_use["data_uses"] = ["advertising"]
        # but also disabling the conflicting existing notice should make the update OK
        patch_privacy_notice_payload["disabled"] = True
        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload,
                patch_privacy_notice_us_ca_updated_data_use,
            ],
        )
        assert resp.status_code == 200

        # but if we try to re-enable that existing notice, we should now get a failure
        patch_privacy_notice_payload["disabled"] = False
        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload,
            ],
        )
        assert resp.status_code == 422

    def test_patch_privacy_notice(
        self,
        api_client: TestClient,
        generate_auth_header,
        patch_privacy_notice_payload: dict[str, Any],
        privacy_notice: PrivacyNotice,
        url,
        db,
    ):
        """
        Test patching a single privacy notice
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        before_update = datetime.now().isoformat()

        resp = api_client.patch(
            url, headers=auth_header, json=[patch_privacy_notice_payload]
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        response_notice = resp.json()[0]

        # assert our response object has the updated values
        assert response_notice["name"] == patch_privacy_notice_payload["name"]
        assert response_notice["id"] == patch_privacy_notice_payload["id"]
        assert response_notice["regions"] == patch_privacy_notice_payload["regions"]
        assert (
            response_notice["consent_mechanism"]
            == patch_privacy_notice_payload["consent_mechanism"]
        )
        assert response_notice["data_uses"] == patch_privacy_notice_payload["data_uses"]
        assert response_notice["version"] == 2.0
        assert response_notice["created_at"] < before_update
        assert response_notice["updated_at"] < datetime.now().isoformat()
        assert response_notice["updated_at"] > before_update
        assert response_notice["disabled"]

        # assert our old history record has the old privacy notice data
        history_record: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db=db)
            .filter(PrivacyNoticeHistory.privacy_notice_id == privacy_notice.id)
            .filter(PrivacyNoticeHistory.version == 1.0)
        ).first()
        assert (
            history_record.name
            == privacy_notice.name
            != patch_privacy_notice_payload["name"]
        )
        assert (
            history_record.regions
            == privacy_notice.regions
            != patch_privacy_notice_payload["regions"]
        )
        assert (
            history_record.consent_mechanism
            == privacy_notice.consent_mechanism
            != patch_privacy_notice_payload["consent_mechanism"]
        )
        assert (
            history_record.data_uses
            == privacy_notice.data_uses
            != patch_privacy_notice_payload["data_uses"]
        )
        assert history_record.version == 1.0
        assert (
            history_record.disabled
            == privacy_notice.disabled
            != patch_privacy_notice_payload["disabled"]
        )

        # assert there's a new history record with the new privacy notice data
        history_record: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db=db)
            .filter(PrivacyNoticeHistory.privacy_notice_id == privacy_notice.id)
            .filter(PrivacyNoticeHistory.version == 2.0)
        ).first()
        assert history_record.name == patch_privacy_notice_payload["name"]
        assert [
            region.value for region in history_record.regions
        ] == patch_privacy_notice_payload["regions"]
        assert (
            history_record.consent_mechanism.value
            == patch_privacy_notice_payload["consent_mechanism"]
        )
        assert history_record.data_uses == patch_privacy_notice_payload["data_uses"]
        assert history_record.version == 2.0
        assert history_record.disabled == patch_privacy_notice_payload["disabled"]

        # assert the db privacy notice record has the updated values
        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        db.refresh(db_notice)

        assert response_notice["name"] == db_notice.name
        assert response_notice["version"] == db_notice.version
        assert response_notice["created_at"] == db_notice.created_at.isoformat()
        assert response_notice["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice["disabled"] == db_notice.disabled
        assert response_notice["regions"] == [
            region.value for region in db_notice.regions
        ]
        assert response_notice["consent_mechanism"] == db_notice.consent_mechanism.value
        assert response_notice["data_uses"] == db_notice.data_uses

    def test_patch_multiple_privacy_notices(
        self,
        api_client: TestClient,
        generate_auth_header,
        patch_privacy_notice_payload: dict[str, Any],
        patch_privacy_notice_payload_us_ca_provide: dict[str, Any],
        privacy_notice: PrivacyNotice,
        privacy_notice_us_ca_provide: PrivacyNotice,
        url,
        db,
    ):
        """
        Test patching multiple privacy notices
        """

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        before_update = datetime.now().isoformat()
        old_name = privacy_notice.name
        old_regions = privacy_notice.regions
        old_consent_mechanism = privacy_notice.consent_mechanism
        old_data_uses = privacy_notice.data_uses

        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload,
                patch_privacy_notice_payload_us_ca_provide,
            ],
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # first response is first request object
        response_notice = resp.json()[0]

        # assert our response object has the updated values
        assert response_notice["name"] == patch_privacy_notice_payload["name"]
        assert response_notice["id"] == patch_privacy_notice_payload["id"]
        assert response_notice["regions"] == patch_privacy_notice_payload["regions"]
        assert (
            response_notice["consent_mechanism"]
            == patch_privacy_notice_payload["consent_mechanism"]
        )
        assert response_notice["data_uses"] == patch_privacy_notice_payload["data_uses"]
        assert response_notice["version"] == 2.0
        assert response_notice["created_at"] < before_update
        assert response_notice["updated_at"] < datetime.now().isoformat()
        assert response_notice["updated_at"] > before_update
        assert response_notice["disabled"]

        # assert a new history record was created and has the new privacy notice data
        history_record: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db=db)
            .filter(PrivacyNoticeHistory.privacy_notice_id == privacy_notice.id)
            .filter(PrivacyNoticeHistory.version == 2.0)
        ).first()
        assert history_record.name == patch_privacy_notice_payload["name"]
        assert [
            region.value for region in history_record.regions
        ] == patch_privacy_notice_payload["regions"]
        assert (
            history_record.consent_mechanism.value
            == patch_privacy_notice_payload["consent_mechanism"]
        )
        assert history_record.data_uses == patch_privacy_notice_payload["data_uses"]
        assert history_record.version == 2.0
        assert history_record.disabled == patch_privacy_notice_payload["disabled"]

        # assert the db privacy notice record has the updated values
        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        db.refresh(db_notice)

        assert response_notice["name"] == db_notice.name
        assert response_notice["version"] == db_notice.version
        assert response_notice["created_at"] == db_notice.created_at.isoformat()
        assert response_notice["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice["disabled"] == db_notice.disabled
        assert response_notice["regions"] == [
            region.value for region in db_notice.regions
        ]
        assert response_notice["consent_mechanism"] == db_notice.consent_mechanism.value
        assert response_notice["data_uses"] == db_notice.data_uses

        # second response is the second request object
        response_notice_2 = resp.json()[1]

        # assert our response object has the updated values
        assert (
            response_notice_2["description"]
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )
        assert (
            response_notice_2["id"] == patch_privacy_notice_payload_us_ca_provide["id"]
        )
        # these response values should still be the old values
        assert response_notice_2["name"] == privacy_notice_us_ca_provide.name
        assert response_notice_2["regions"] == [
            region.value for region in privacy_notice_us_ca_provide.regions
        ]
        assert (
            response_notice_2["consent_mechanism"]
            == privacy_notice_us_ca_provide.consent_mechanism.value
        )
        assert response_notice_2["data_uses"] == privacy_notice_us_ca_provide.data_uses
        assert response_notice_2["version"] == 2.0
        assert response_notice_2["created_at"] < before_update
        assert response_notice_2["updated_at"] < datetime.now().isoformat()
        assert response_notice_2["updated_at"] > before_update
        assert not response_notice_2["disabled"]

        # assert a new history record was created and has the new privacy notice data
        history_record_2: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db=db)
            .filter(
                PrivacyNoticeHistory.privacy_notice_id
                == privacy_notice_us_ca_provide.id
            )
            .filter(PrivacyNoticeHistory.version == 2.0)
        ).first()
        assert history_record_2.name == privacy_notice_us_ca_provide.name
        assert history_record_2.regions == privacy_notice_us_ca_provide.regions
        assert (
            history_record_2.consent_mechanism
            == privacy_notice_us_ca_provide.consent_mechanism
        )
        assert history_record_2.data_uses == privacy_notice_us_ca_provide.data_uses
        assert (
            history_record_2.description
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )
        assert history_record_2.origin is None
        assert history_record_2.version == 2.0
        assert history_record_2.disabled == privacy_notice_us_ca_provide.disabled

        # assert the db privacy notice record has the updated values
        db_notice_2: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice_2["id"]
        )
        db.refresh(db_notice_2)

        assert response_notice_2["name"] == db_notice_2.name
        assert response_notice_2["version"] == db_notice_2.version
        assert response_notice_2["description"] == db_notice_2.description
        assert response_notice_2["origin"] == db_notice_2.origin
        assert response_notice_2["created_at"] == db_notice_2.created_at.isoformat()
        assert response_notice_2["updated_at"] == db_notice_2.updated_at.isoformat()
        assert response_notice_2["disabled"] == db_notice_2.disabled
        assert response_notice_2["regions"] == [
            region.value for region in db_notice_2.regions
        ]
        assert (
            response_notice_2["consent_mechanism"]
            == db_notice_2.consent_mechanism.value
        )
        assert response_notice_2["data_uses"] == db_notice_2.data_uses

    def test_patching_privacy_notice_twice(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_notice_us_ca_provide: PrivacyNotice,
        patch_privacy_notice_payload_us_ca_provide: dict[str, Any],
        url,
        db,
    ):
        """
        Test patching a single privacy notice twice to ensure we can continue to update it
        """

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_UPDATE])

        # our first patch, just like above

        before_update = datetime.now().isoformat()

        resp = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload_us_ca_provide,
            ],
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        response_notice = resp.json()[0]

        # assert our response object has the updated values
        assert (
            response_notice["description"]
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )
        assert response_notice["id"] == patch_privacy_notice_payload_us_ca_provide["id"]
        assert response_notice["version"] == 2.0
        assert response_notice["created_at"] < before_update
        assert response_notice["updated_at"] < datetime.now().isoformat()
        assert response_notice["updated_at"] > before_update

        # assert a history record was created and has the new privacy notice data
        history_record: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db=db)
            .filter(
                PrivacyNoticeHistory.privacy_notice_id
                == privacy_notice_us_ca_provide.id
            )
            .filter(PrivacyNoticeHistory.version == 2.0)
        ).first()
        assert history_record.name == privacy_notice_us_ca_provide.name
        assert history_record.regions == privacy_notice_us_ca_provide.regions
        assert (
            history_record.consent_mechanism
            == privacy_notice_us_ca_provide.consent_mechanism
        )
        assert history_record.data_uses == privacy_notice_us_ca_provide.data_uses
        assert (
            history_record.description
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )
        assert history_record.origin is None
        assert history_record.version == 2.0
        assert history_record.disabled == privacy_notice_us_ca_provide.disabled

        # assert the db privacy notice record has the updated values
        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        db.refresh(db_notice)

        assert response_notice["name"] == db_notice.name
        assert response_notice["version"] == db_notice.version
        assert response_notice["description"] == db_notice.description
        assert response_notice["origin"] == db_notice.origin
        assert response_notice["created_at"] == db_notice.created_at.isoformat()
        assert response_notice["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice["disabled"] == db_notice.disabled
        assert response_notice["regions"] == [
            region.value for region in db_notice.regions
        ]
        assert response_notice["consent_mechanism"] == db_notice.consent_mechanism.value
        assert response_notice["data_uses"] == db_notice.data_uses

        # now our second patch

        before_update_2 = datetime.now().isoformat()
        # add in an update for the 'name' field this time
        # keep old name in order to check history record
        old_name = db_notice.name
        patch_privacy_notice_payload_us_ca_provide["name"] = "an updated name"

        resp_2 = api_client.patch(
            url,
            headers=auth_header,
            json=[
                patch_privacy_notice_payload_us_ca_provide,
            ],
        )
        assert resp_2.status_code == 200
        assert len(resp_2.json()) == 1

        response_notice_2 = resp_2.json()[0]

        # assert our response object has the updated values
        assert (
            response_notice_2["description"]
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )  # description was still on our patch payload, even though this is a no-op
        assert (
            response_notice_2["name"]
            == patch_privacy_notice_payload_us_ca_provide["name"]
        )  # name was actually udpated, so this is an important check
        assert (
            response_notice_2["id"] == patch_privacy_notice_payload_us_ca_provide["id"]
        )
        assert response_notice_2["version"] == 3.0
        assert response_notice_2["created_at"] < before_update
        assert response_notice_2["updated_at"] < datetime.now().isoformat()
        assert response_notice_2["updated_at"] > before_update_2

        # assert a third history record was created and has the new privacy notice data
        assert (
            len(
                PrivacyNoticeHistory.query(db)
                .filter(
                    PrivacyNoticeHistory.privacy_notice_id
                    == privacy_notice_us_ca_provide.id
                )
                .all()
            )
            == 3
        )  # should have 3 history records now pointing to this notice
        history_record_3: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db)
            .filter(
                PrivacyNoticeHistory.privacy_notice_id
                == privacy_notice_us_ca_provide.id
            )
            .filter(PrivacyNoticeHistory.version == 3.0)
            .first()
        )  # find the latest history record
        assert history_record_3.name == "an updated name"
        assert history_record_3.regions == privacy_notice_us_ca_provide.regions
        assert (
            history_record_3.consent_mechanism
            == privacy_notice_us_ca_provide.consent_mechanism
        )
        assert history_record_3.data_uses == privacy_notice_us_ca_provide.data_uses
        assert (
            history_record_3.description
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )
        assert history_record_3.version == 3.0
        assert history_record_3.disabled == privacy_notice_us_ca_provide.disabled

        # assert old history record hasn't changed
        history_record_2: PrivacyNoticeHistory = (
            PrivacyNoticeHistory.query(db)
            .filter(
                PrivacyNoticeHistory.privacy_notice_id
                == privacy_notice_us_ca_provide.id
            )
            .filter(PrivacyNoticeHistory.version == 2.0)
            .first()
        )
        assert history_record_2.name == old_name
        assert history_record_2.regions == privacy_notice_us_ca_provide.regions
        assert (
            history_record_2.consent_mechanism
            == privacy_notice_us_ca_provide.consent_mechanism
        )
        assert history_record_2.data_uses == privacy_notice_us_ca_provide.data_uses
        assert (
            history_record_2.description
            == patch_privacy_notice_payload_us_ca_provide["description"]
        )
        assert history_record_2.version == 2.0
        assert history_record_2.disabled == privacy_notice_us_ca_provide.disabled

        # assert the db privacy notice record has the updated values
        db_notice: PrivacyNotice = PrivacyNotice.get(
            db=db, object_id=response_notice["id"]
        )
        db.refresh(db_notice)

        assert response_notice_2["name"] == db_notice.name
        assert response_notice_2["version"] == db_notice.version
        assert response_notice_2["description"] == db_notice.description
        assert response_notice_2["origin"] == db_notice.origin
        assert response_notice_2["created_at"] == db_notice.created_at.isoformat()
        assert response_notice_2["updated_at"] == db_notice.updated_at.isoformat()
        assert response_notice_2["disabled"] == db_notice.disabled
        assert response_notice_2["regions"] == [
            region.value for region in db_notice.regions
        ]
        assert (
            response_notice_2["consent_mechanism"] == db_notice.consent_mechanism.value
        )
        assert response_notice_2["data_uses"] == db_notice.data_uses
