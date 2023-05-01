from __future__ import annotations

from typing import List

import pytest
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.ops.api.v1 import scope_registry as scopes
from fides.api.ops.api.v1.endpoints.privacy_experience_endpoints import (
    get_privacy_experience_or_error,
)
from fides.api.ops.api.v1.urn_registry import (
    PRIVACY_EXPERIENCE,
    PRIVACY_EXPERIENCE_DETAIL,
    V1_URL_PREFIX,
)
from fides.api.ops.models.privacy_experience import ComponentType, DeliveryMechanism
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion


class TestGetPrivacyExperiences:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_EXPERIENCE

    def test_get_privacy_experiences_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_privacy_experiences_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_200_OK),
            ("viewer", HTTP_200_OK),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_get_privacy_experience_with_roles(
        self, role, expected_status, api_client: TestClient, url, generate_role_header
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == expected_status

    def test_get_privacy_experiences(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_notice,
        privacy_experience_privacy_center_link,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert one experience in the response
        assert data["total"] == 1
        assert len(data["items"]) == 1
        resp = data["items"][0]

        assert resp["disabled"] is False
        assert resp["component"] == "privacy_center"
        assert resp["delivery_mechanism"] == "link"
        assert resp["regions"] == ["us_ca", "us_co"]
        assert resp["component_title"] == "Manage your consent preferences"
        assert (
            resp["component_description"]
            == "On this page you can opt in and out of these data uses cases"
        )
        assert resp["banner_title"] is None
        assert resp["banner_description"] is None
        assert resp["link_label"] == "Manage your privacy"
        assert resp["confirmation_button_label"] is None
        assert resp["reject_button_label"] is None
        assert resp["acknowledgement_button_label"] is None
        assert resp["id"] is not None
        assert resp["version"] == 1
        assert resp["privacy_experience_history_id"] is not None
        assert resp["privacy_experience_template_id"] is None
        assert (
            resp["privacy_experience_history_id"]
            == privacy_experience_privacy_center_link.privacy_experience_history_id
        )
        assert len(resp["privacy_notices"]) == 1
        assert resp["privacy_notices"][0]["id"] == privacy_notice.id

    def test_get_privacy_experiences_show_disabled_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

        resp = api_client.get(
            url + "?show_disabled=False",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_privacy_center_link.id,
            privacy_experience_overlay_link.id,
        }

        assert privacy_experience_overlay_banner.id not in {
            exp["id"] for exp in data["items"]
        }

    def test_get_privacy_experiences_region_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?region=eu_fr",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == privacy_experience_overlay_link.id
        assert data["items"][0]["regions"] == [
            reg.value for reg in privacy_experience_overlay_link.regions
        ]
        resp = api_client.get(
            url + "?region=us_ca",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_privacy_center_link.id,
            privacy_experience_overlay_banner.id,
        }

        resp = api_client.get(
            url + "?region=bad_region",
            headers=auth_header,
        )
        assert resp.status_code == 422

        resp = api_client.get(
            url + "?region=eu_it",
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_get_privacy_experiences_components_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?component=overlay",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_overlay_link.id,
            privacy_experience_overlay_banner.id,
        }

        resp = api_client.get(
            url + "?component=privacy_center",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_privacy_center_link.id
        }

        resp = api_client.get(
            url + "?component=bad_type",
            headers=auth_header,
        )
        assert resp.status_code == 422

    @pytest.mark.usefixtures(
        "privacy_experience_privacy_center_link",
        "privacy_experience_overlay_link",
        "privacy_experience_overlay_banner",
    )
    def test_get_privacy_experiences_has_notices_no_notices(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?has_notices=True",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.usefixtures(
        "privacy_experience_privacy_center_link",
        "privacy_experience_overlay_link",
        "privacy_experience_overlay_banner",
        "privacy_notice_eu_cy_provide_service_frontend_only",
    )
    def test_get_privacy_experiences_has_notices_no_regions_overlap(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?has_notices=True",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.usefixtures(
        "privacy_notice_us_co_provide_service_operations",  # not displayed in overlay or privacy center
        "privacy_notice_eu_cy_provide_service_frontend_only",  # doesn't overlap with any regions
    )
    def test_get_privacy_experiences_has_notices(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
        privacy_notice_eu_fr_provide_service_frontend_only,
        privacy_notice_us_ca_provide,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?has_notices=True",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3

        first_experience = data["items"][0]
        assert (
            first_experience["id"] == privacy_experience_overlay_banner.id
        )  # Most recently created
        assert first_experience["component"] == "overlay"
        assert first_experience["regions"] == ["us_ca"]
        assert len(first_experience["privacy_notices"]) == 2

        # Notices match on region and "overlay"
        privacy_experience_overlay_notice_1 = first_experience["privacy_notices"][0]
        assert (
            privacy_experience_overlay_notice_1["id"] == privacy_notice_us_ca_provide.id
        )
        assert privacy_experience_overlay_notice_1["regions"] == ["us_ca"]
        assert privacy_experience_overlay_notice_1["displayed_in_overlay"]

        privacy_experience_overlay_notice_2 = first_experience["privacy_notices"][1]
        assert privacy_experience_overlay_notice_2["id"] == privacy_notice.id
        assert privacy_experience_overlay_notice_2["regions"] == ["us_ca", "us_co"]
        assert privacy_experience_overlay_notice_2["displayed_in_overlay"]

        second_experience = data["items"][1]
        assert (
            second_experience["id"] == privacy_experience_overlay_link.id
        )  # Most recently created
        assert second_experience["component"] == "overlay"
        assert second_experience["regions"] == ["eu_fr"]
        assert len(second_experience["privacy_notices"]) == 1

        # Notices match on region and "overlay"
        privacy_experience_overlay_link_notice_1 = second_experience["privacy_notices"][
            0
        ]
        assert (
            privacy_experience_overlay_link_notice_1["id"]
            == privacy_notice_eu_fr_provide_service_frontend_only.id
        )
        assert privacy_experience_overlay_link_notice_1["regions"] == ["eu_fr"]
        assert privacy_experience_overlay_link_notice_1["displayed_in_overlay"]

        third_experience = data["items"][2]
        assert (
            third_experience["id"] == privacy_experience_privacy_center_link.id
        )  # Most recently created
        assert third_experience["component"] == "privacy_center"
        assert third_experience["regions"] == ["us_ca", "us_co"]
        assert len(third_experience["privacy_notices"]) == 2

        # Notices match on region and "overlay"
        privacy_experience_privacy_center_notice_1 = third_experience[
            "privacy_notices"
        ][0]
        assert (
            privacy_experience_privacy_center_notice_1["id"]
            == privacy_notice_us_co_third_party_sharing.id
        )
        assert privacy_experience_privacy_center_notice_1["regions"] == ["us_co"]
        assert privacy_experience_privacy_center_notice_1["displayed_in_privacy_center"]

        privacy_experience_privacy_center_notice_2 = third_experience[
            "privacy_notices"
        ][1]
        assert privacy_experience_privacy_center_notice_2["id"] == privacy_notice.id
        assert privacy_experience_privacy_center_notice_2["regions"] == [
            "us_ca",
            "us_co",
        ]
        assert privacy_experience_privacy_center_notice_2["displayed_in_privacy_center"]

    @pytest.mark.usefixtures(
        "privacy_notice_us_co_provide_service_operations",  # not displayed in overlay or privacy center
        "privacy_notice_eu_cy_provide_service_frontend_only",  # doesn't overlap with any regions,
        "privacy_experience_overlay_link",  # eu_fr, not co
        "privacy_experience_overlay_banner",  # us_ca, not co
        "privacy_notice_eu_fr_provide_service_frontend_only",  # eu_fr
        "privacy_notice_us_ca_provide",  # us_ca
    )
    def test_filter_on_notices_and_region(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
    ):
        """Region filter propagates through to the notices too"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?has_notices=True&region=us_co",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1

        assert data["items"][0]["id"] == privacy_experience_privacy_center_link.id
        assert data["items"][0]["regions"] == ["us_ca", "us_co"]

        notices = data["items"][0]["privacy_notices"]
        assert len(notices) == 2
        assert notices[0]["regions"] == ["us_co"]
        assert notices[0]["id"] == privacy_notice_us_co_third_party_sharing.id
        assert notices[0]["displayed_in_privacy_center"]

        assert notices[1]["regions"] == ["us_ca", "us_co"]
        assert notices[1]["id"] == privacy_notice.id
        assert notices[1]["displayed_in_privacy_center"]

    @pytest.mark.usefixtures(
        "privacy_notice_us_co_provide_service_operations",  # not displayed in overlay or privacy center
        "privacy_notice_eu_cy_provide_service_frontend_only",  # doesn't overlap with any regions,
        "privacy_experience_overlay_link",  # eu_fr, not co
        "privacy_experience_overlay_banner",  # us_ca, not co
        "privacy_notice_eu_fr_provide_service_frontend_only",  # eu_fr
        "privacy_notice_us_ca_provide",  # us_ca
    )
    def test_filter_on_notices_and_region_and_show_disabled_is_false(
        self,
        api_client: TestClient,
        generate_auth_header,
        db,
        url,
        privacy_experience_privacy_center_link,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
    ):
        """Region filter propagates through to the notices too"""
        privacy_notice_us_co_third_party_sharing.disabled = True
        privacy_notice_us_co_third_party_sharing.save(db)

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            url + "?has_notices=True&region=us_co&show_disabled=False",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1

        assert data["items"][0]["id"] == privacy_experience_privacy_center_link.id
        assert data["items"][0]["regions"] == ["us_ca", "us_co"]

        notices = data["items"][0]["privacy_notices"]
        assert len(notices) == 1
        assert notices[0]["regions"] == ["us_ca", "us_co"]
        assert notices[0]["id"] == privacy_notice.id
        assert notices[0]["displayed_in_privacy_center"]


class TestCreatePrivacyExperiences:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_EXPERIENCE

    @pytest.fixture(scope="function")
    def request_data(self) -> List[dict]:
        return [
            {
                "component": "overlay",
                "delivery_mechanism": "banner",
                "regions": ["eu_it", "eu_es", "eu_fr"],
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            }
        ]

    def test_create_privacy_experiences_unauthenticated(self, url, api_client):
        resp = api_client.post(url)
        assert resp.status_code == 401

    def test_create_privacy_experiences_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.post(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_201_CREATED),
            ("contributor", HTTP_201_CREATED),
            ("viewer_and_approver", HTTP_403_FORBIDDEN),
            ("viewer", HTTP_403_FORBIDDEN),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_create_privacy_experience_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
        request_data,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.post(url, json=request_data, headers=auth_header)
        assert response.status_code == expected_status

    def test_post_privacy_experience_duplicate_regions(
        self,
        api_client: TestClient,
        generate_auth_header,
        request_data,
        url,
    ):
        """
        Assert if regions are accidentally duplicated on a notice that this is flagged
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_CREATE])
        last_region = request_data[0]["regions"][-1]
        request_data[0]["regions"].append(last_region)

        resp = api_client.post(url, headers=auth_header, json=request_data)
        assert resp.status_code == 422
        assert resp.json()["detail"][0]["msg"] == "Duplicate regions found."

    @pytest.mark.usefixtures("privacy_notice")
    def test_create_privacy_experiences(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        url,
        request_data,
        privacy_notice_eu_fr_provide_service_frontend_only,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_CREATE])

        resp = api_client.post(url, headers=auth_header, json=request_data)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 1
        data = data[0]
        assert data["disabled"] is False
        assert data["component"] == "overlay"
        assert data["delivery_mechanism"] == "banner"
        assert data["regions"] == ["eu_it", "eu_es", "eu_fr"]
        assert data["component_title"] == "Control your privacy"
        assert (
            data["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert data["banner_title"] == "Manage your consent"
        assert (
            data["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert data["link_label"] is None
        assert data["confirmation_button_label"] == "Accept all"
        assert data["reject_button_label"] == "Reject all"
        assert data["acknowledgement_button_label"] is None
        assert data["version"] == 1.0
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

        assert len(data["privacy_notices"]) == 1
        assert (
            data["privacy_notices"][0]["id"]
            == privacy_notice_eu_fr_provide_service_frontend_only.id
        )

        created_privacy_experience_id = data["id"]
        experience = get_privacy_experience_or_error(
            db, experience_id=created_privacy_experience_id
        )

        # Assert qualities of associated created experience
        assert experience.histories.count() == 1
        history = experience.histories[0]
        assert data["privacy_experience_history_id"] == history.id
        assert history.privacy_experience_id == experience.id
        assert history.version == 1.0
        assert not history.disabled
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.regions == [
            PrivacyNoticeRegion.eu_it,
            PrivacyNoticeRegion.eu_es,
            PrivacyNoticeRegion.eu_fr,
        ]
        assert history.component_title == "Control your privacy"
        assert (
            history.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert history.banner_title == "Manage your consent"
        assert history.link_label is None
        assert history.confirmation_button_label == "Accept all"
        assert history.reject_button_label == "Reject all"
        assert history.acknowledgement_button_label is None
        assert history.version == 1.0
        assert history.created_at is not None
        assert history.updated_at is not None

        db.delete(history)
        db.delete(experience)


class TestPrivacyExperienceDetail:
    @pytest.fixture(scope="function")
    def url(self, privacy_experience_overlay_banner) -> str:
        return V1_URL_PREFIX + PRIVACY_EXPERIENCE_DETAIL.format(
            privacy_experience_id=privacy_experience_overlay_banner.id
        )

    def test_get_privacy_experience_detail_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_privacy_experience_detail_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_NOTICE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_200_OK),
            ("viewer", HTTP_200_OK),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_get_privacy_experience_detail_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == expected_status

    def test_get_privacy_experience_bad_experience(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.get(
            V1_URL_PREFIX
            + PRIVACY_EXPERIENCE_DETAIL.format(privacy_experience_id="bad_id"),
            headers=auth_header,
        )
        assert resp.status_code == 404

    @pytest.mark.usefixtures(
        "privacy_notice", "privacy_notice_eu_fr_provide_service_frontend_only"
    )
    def test_get_privacy_experience_detail(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_overlay_banner,
        privacy_notice_us_ca_provide,
        privacy_notice,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200
        body = resp.json()

        assert body["disabled"] is True
        assert body["component"] == "overlay"
        assert body["delivery_mechanism"] == "banner"
        assert body["regions"] == ["us_ca"]
        assert body["component_title"] == "Manage your consent"
        assert (
            body["component_description"]
            == "On this page you can opt in and out of these data uses cases"
        )
        assert body["banner_title"] == "Manage your consent"
        assert (
            body["banner_description"]
            == "We use cookies to recognize visitors and remember their preferences"
        )
        assert body["link_label"] is None
        assert body["confirmation_button_label"] == "Accept all"
        assert body["reject_button_label"] == "Reject all"
        assert body["acknowledgement_button_label"] is None
        assert body["id"] == privacy_experience_overlay_banner.id
        assert body["created_at"] is not None
        assert body["updated_at"] is not None
        assert body["version"] is not None
        assert (
            body["privacy_experience_history_id"]
            == privacy_experience_overlay_banner.histories[0].id
        )
        assert len(body["privacy_notices"]) == 2
        assert body["privacy_notices"][0]["id"] == privacy_notice_us_ca_provide.id
        assert body["privacy_notices"][1]["id"] == privacy_notice.id

    @pytest.mark.usefixtures(
        "privacy_notice", "privacy_notice_eu_fr_provide_service_frontend_only"
    )
    def test_get_privacy_experience_detail_bad_region_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_overlay_banner,
    ):
        """Region filter for an experience can restrict embedded notices to just that region"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])

        resp = api_client.get(url + "?region=eu_it", headers=auth_header)
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == f"Region query param eu_it not applicable for privacy experience {privacy_experience_overlay_banner.id}."
        )

    @pytest.mark.usefixtures("privacy_notice_eu_fr_provide_service_frontend_only")
    def test_get_privacy_experience_detail_region_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,  # regions ca/co
        privacy_notice,  # regions ca/co,
        privacy_notice_us_co_third_party_sharing,  # regions co
    ):
        """Region filter for an experience can restrict embedded notices to just that region"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])

        resp = api_client.get(
            V1_URL_PREFIX
            + PRIVACY_EXPERIENCE_DETAIL.format(
                privacy_experience_id=privacy_experience_privacy_center_link.id
            ),
            headers=auth_header,
        )
        # Sanity check
        assert resp.status_code == 200
        assert len(resp.json()["privacy_notices"]) == 2
        assert resp.json()["id"] == privacy_experience_privacy_center_link.id
        assert (
            resp.json()["privacy_notices"][0]["id"]
            == privacy_notice_us_co_third_party_sharing.id
        )
        assert resp.json()["privacy_notices"][1]["id"] == privacy_notice.id

        # Now filter just on ca to get just the ca notices
        resp = api_client.get(
            V1_URL_PREFIX
            + PRIVACY_EXPERIENCE_DETAIL.format(
                privacy_experience_id=privacy_experience_privacy_center_link.id
            )
            + "?region=us_ca",
            headers=auth_header,
        )
        assert len(resp.json()["privacy_notices"]) == 1
        assert resp.json()["id"] == privacy_experience_privacy_center_link.id
        assert resp.json()["privacy_notices"][0]["id"] == privacy_notice.id

    @pytest.mark.usefixtures(
        "privacy_notice", "privacy_notice_eu_fr_provide_service_frontend_only"
    )
    def test_get_privacy_experience_detail_bad_show_disabled_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db,
        privacy_experience_overlay_banner,
    ):
        """Show_disabled=False can be added to privacy experience detail to only return enabled privacy notices for an experience.
        However, if the experience itself is disabled, this is an invalid filter.
        """
        privacy_experience_overlay_banner.disabled = True
        privacy_experience_overlay_banner.save(db)
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])

        resp = api_client.get(url + "?show_disabled=False", headers=auth_header)
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == f"Query param show_disabled=False not applicable for disabled privacy experience {privacy_experience_overlay_banner.id}."
        )

    @pytest.mark.usefixtures(
        "privacy_notice", "privacy_notice_eu_fr_provide_service_frontend_only"
    )
    def test_get_privacy_experience_detail_disabled_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db,
        privacy_notice,
        privacy_notice_us_ca_provide,
        privacy_experience_overlay_banner,
    ):
        """Show_disabled=False can be added to privacy experience detail to only return enabled privacy notices for an experience."""
        privacy_experience_overlay_banner.disabled = False
        privacy_experience_overlay_banner.save(db)
        privacy_notice.disabled = True
        privacy_notice.save(db)

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])

        resp = api_client.get(url, headers=auth_header)

        # Sanity check
        assert resp.status_code == 200
        assert len(resp.json()["privacy_notices"]) == 2
        assert resp.json()["id"] == privacy_experience_overlay_banner.id
        assert (
            resp.json()["privacy_notices"][0]["id"] == privacy_notice_us_ca_provide.id
        )
        assert resp.json()["privacy_notices"][0]["disabled"] is False
        assert resp.json()["privacy_notices"][1]["id"] == privacy_notice.id
        assert resp.json()["privacy_notices"][1]["disabled"] is True

        # Now filter just on ca to get just the ca notices
        resp = api_client.get(
            url + "?show_disabled=False",
            headers=auth_header,
        )
        assert len(resp.json()["privacy_notices"]) == 1
        assert resp.json()["id"] == privacy_experience_overlay_banner.id
        assert (
            resp.json()["privacy_notices"][0]["id"] == privacy_notice_us_ca_provide.id
        )

        assert resp.json()["privacy_notices"][0]["disabled"] is False


class TestUpdatePrivacyExperiences:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_EXPERIENCE

    @pytest.fixture(scope="function")
    def request_data(self, privacy_experience_privacy_center_link) -> List[dict]:
        return [
            {
                "component": ComponentType.privacy_center.value,
                "delivery_mechanism": DeliveryMechanism.link.value,
                "regions": [
                    PrivacyNoticeRegion.us_ca.value,
                    PrivacyNoticeRegion.us_co.value,
                    PrivacyNoticeRegion.us_va.value,
                ],
                "component_title": "Manage your consent preferences with Fides!",
                "id": privacy_experience_privacy_center_link.id,
            }
        ]

    def test_update_privacy_experiences_unauthenticated(self, url, api_client):
        resp = api_client.patch(url)
        assert resp.status_code == 401

    def test_update_privacy_experiences_wrong_scope(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        request_data,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.patch(
            url,
            json=request_data,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_403_FORBIDDEN),
            ("viewer", HTTP_403_FORBIDDEN),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_update_privacy_experience_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
        request_data,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.patch(url, json=request_data, headers=auth_header)
        assert response.status_code == expected_status

    def test_update_privacy_experiences_duplicate_ids(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        url,
        request_data,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        dupe = request_data[0]
        request_data.append(dupe)
        resp = api_client.patch(url, headers=auth_header, json=request_data)
        assert resp.status_code == 422
        assert (
            resp.json()["detail"]
            == "Duplicate privacy experience ids submitted in request."
        )

    def test_update_privacy_experiences_bad_ids(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        url,
        request_data,
    ):
        request_data[0]["id"] = "bad_id"
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        resp = api_client.patch(url, headers=auth_header, json=request_data)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "No PrivacyExperience found for id bad_id."

    def test_update_privacy_experiences(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        url,
        request_data,
        privacy_notice,
        privacy_experience_privacy_center_link,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])

        resp = api_client.patch(url, headers=auth_header, json=request_data)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        data = data[0]
        assert data["disabled"] is False
        assert data["component"] == "privacy_center"
        assert data["delivery_mechanism"] == "link"
        assert data["regions"] == ["us_ca", "us_co", "us_va"]
        assert data["component_title"] == "Manage your consent preferences with Fides!"
        assert (
            data["component_description"]
            == privacy_experience_privacy_center_link.component_description
        )
        assert data["banner_title"] is None
        assert data["banner_description"] is None
        assert data["link_label"] == "Manage your privacy"
        assert data["confirmation_button_label"] is None
        assert data["reject_button_label"] is None
        assert data["acknowledgement_button_label"] is None
        assert data["version"] == 2.0
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

        assert len(data["privacy_notices"]) == 1
        assert data["privacy_notices"][0]["id"] == privacy_notice.id

        db.refresh(privacy_experience_privacy_center_link)

        # Assert qualities of associated created experience
        assert privacy_experience_privacy_center_link.histories.count() == 2
        history = privacy_experience_privacy_center_link.histories[1]
        assert data["privacy_experience_history_id"] == history.id
        assert (
            history.privacy_experience_id == privacy_experience_privacy_center_link.id
        )
        assert history.version == 2.0
        assert not history.disabled
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.regions == [
            PrivacyNoticeRegion.us_ca,
            PrivacyNoticeRegion.us_co,
            PrivacyNoticeRegion.us_va,
        ]
        assert history.component_title == "Manage your consent preferences with Fides!"
        assert (
            history.component_description
            == "On this page you can opt in and out of these data uses cases"
        )
        assert history.banner_title is None
        assert history.link_label == "Manage your privacy"
        assert history.confirmation_button_label is None
        assert history.reject_button_label is None
        assert history.acknowledgement_button_label is None
        assert history.version == 2.0
        assert history.created_at is not None
        assert history.updated_at is not None
