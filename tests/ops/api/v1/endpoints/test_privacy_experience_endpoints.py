from __future__ import annotations

import pytest
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.ops.api.v1 import scope_registry as scopes
from fides.api.ops.api.v1.endpoints.privacy_experience_endpoints import (
    get_experience_config_or_error,
)
from fides.api.ops.api.v1.urn_registry import (
    EXPERIENCE_CONFIG,
    PRIVACY_EXPERIENCE,
    PRIVACY_EXPERIENCE_DETAIL,
    V1_URL_PREFIX,
)
from fides.api.ops.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    PrivacyExperience,
    PrivacyExperienceConfig,
)
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
)


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
        assert resp["region"] == "us_co"
        assert resp["version"] == 1.0
        # Assert experience config is nested
        experience_config = resp["experience_config"]
        assert experience_config["component_title"] == "Control your privacy"
        assert experience_config["banner_title"] is None
        assert experience_config["banner_description"] is None
        assert experience_config["link_label"] == "Manage your preferences"
        assert experience_config["confirmation_button_label"] is None
        assert experience_config["reject_button_label"] is None
        assert experience_config["acknowledgement_button_label"] is None
        assert experience_config["id"] is not None
        assert experience_config["version"] == 1
        assert (
            experience_config["experience_config_history_id"]
            == privacy_experience_privacy_center_link.experience_config.experience_config_history_id
        )
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
        assert data["items"][0]["region"] == "eu_fr"
        resp = api_client.get(
            url + "?region=us_ca",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
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
        assert first_experience["region"] == "us_ca"
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
        assert second_experience["region"] == "eu_fr"
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
        assert third_experience["region"] == "us_co"
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
        assert data["items"][0]["region"] == "us_co"

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
        assert data["items"][0]["region"] == "us_co"

        notices = data["items"][0]["privacy_notices"]
        assert len(notices) == 1
        assert notices[0]["regions"] == ["us_ca", "us_co"]
        assert notices[0]["id"] == privacy_notice.id
        assert notices[0]["displayed_in_privacy_center"]


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
        assert body["region"] == "us_ca"
        experience_config = body["experience_config"]
        assert experience_config["component_title"] == "Manage your consent"
        assert (
            experience_config["component_description"]
            == "On this page you can opt in and out of these data uses cases"
        )
        assert experience_config["banner_title"] == "Manage your consent"
        assert (
            experience_config["banner_description"]
            == "We use cookies to recognize visitors and remember their preferences"
        )
        assert experience_config["link_label"] is None
        assert experience_config["confirmation_button_label"] == "Accept all"
        assert experience_config["reject_button_label"] == "Reject all"
        assert experience_config["acknowledgement_button_label"] is None
        assert experience_config["id"] is not None
        assert experience_config["version"] == 1.0
        assert (
            experience_config["experience_config_history_id"]
            == privacy_experience_overlay_banner.experience_config_history_id
        )

        assert body["id"] == privacy_experience_overlay_banner.id
        assert body["created_at"] is not None
        assert body["updated_at"] is not None
        assert body["version"] == 1.0
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


class TestGetExperienceConfigList:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + EXPERIENCE_CONFIG

    def test_get_experience_config_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_experience_config_wrong_scope(
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
    def test_get_experience_config_with_roles(
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

    @pytest.mark.usefixtures(
        "privacy_experience_overlay_link", "privacy_experience_overlay_banner"
    )
    def test_get_experience_config_list(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        experience_config_overlay_link,
        experience_config_overlay_banner,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()
        assert resp["total"] == 2
        assert resp["page"] == 1
        assert resp["size"] == 50
        data = resp["items"]
        assert len(data) == 2

        first_config = data[0]
        assert first_config["id"] == experience_config_overlay_banner.id
        assert first_config["component"] == "overlay"
        assert first_config["delivery_mechanism"] == "banner"
        assert first_config["disabled"] is True
        assert first_config["regions"] == ["us_ca"]
        assert first_config["version"] == 1.0
        assert first_config["created_at"] is not None
        assert first_config["updated_at"] is not None
        assert (
            first_config["experience_config_history_id"]
            == experience_config_overlay_banner.experience_config_history_id
        )
        assert first_config["banner_title"] == "Manage your consent"

        second_config = data[1]
        assert second_config["id"] == experience_config_overlay_link.id
        assert second_config["component"] == "overlay"
        assert second_config["delivery_mechanism"] == "link"
        assert second_config["disabled"] is False
        assert second_config["regions"] == ["eu_fr"]
        assert second_config["created_at"] is not None
        assert second_config["updated_at"] is not None
        assert second_config["version"] == 1.0
        assert (
            second_config["experience_config_history_id"]
            == experience_config_overlay_link.experience_config_history_id
        )
        assert second_config["link_label"] == "Manage your privacy"

    @pytest.mark.usefixtures(
        "privacy_experience_overlay_link",
        "experience_config_overlay_banner",
        "privacy_experience_overlay_banner",
    )
    def test_get_experience_config_show_disabled_false_filter(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        experience_config_overlay_link,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        response = api_client.get(
            url + "?show_disabled=False",
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()
        assert resp["total"] == 1
        assert resp["page"] == 1
        assert resp["size"] == 50
        data = resp["items"]
        assert len(data) == 1

        config = data[0]
        assert config["id"] == experience_config_overlay_link.id
        assert config["component"] == "overlay"
        assert config["delivery_mechanism"] == "link"
        assert config["disabled"] is False
        assert config["regions"] == ["eu_fr"]
        assert config["version"] == 1.0
        assert config["created_at"] is not None
        assert config["updated_at"] is not None
        assert (
            config["experience_config_history_id"]
            == experience_config_overlay_link.experience_config_history_id
        )
        assert config["link_label"] == "Manage your privacy"

    @pytest.mark.usefixtures(
        "privacy_experience_overlay_link",
        "experience_config_overlay_link",
        "privacy_experience_overlay_banner",
    )
    def test_get_experience_config_region_filter(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        experience_config_overlay_banner,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        response = api_client.get(
            url + "?region=us_ca",
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()
        assert resp["total"] == 1
        assert resp["page"] == 1
        assert resp["size"] == 50
        data = resp["items"]
        assert len(data) == 1

        first_config = data[0]
        assert first_config["id"] == experience_config_overlay_banner.id
        assert first_config["regions"] == ["us_ca"]
        assert first_config["version"] == 1.0
        assert first_config["created_at"] is not None
        assert first_config["updated_at"] is not None
        assert (
            first_config["experience_config_history_id"]
            == experience_config_overlay_banner.experience_config_history_id
        )

    @pytest.mark.usefixtures(
        "privacy_experience_overlay_banner",
        "privacy_experience_overlay_link",
        "privacy_experience_privacy_center_link",
    )
    def test_get_experience_config_component_filter(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        experience_config_overlay_banner,
        experience_config_overlay_link,
        experience_config_privacy_center,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        response = api_client.get(
            url + "?component=overlay",
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()
        assert resp["total"] == 2
        assert resp["page"] == 1
        assert resp["size"] == 50
        data = resp["items"]
        assert len(data) == 2

        assert data[0]["id"] == experience_config_overlay_link.id
        assert data[1]["id"] == experience_config_overlay_banner.id

        response = api_client.get(
            url + "?component=privacy_center",
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()
        assert resp["total"] == 1
        assert resp["page"] == 1
        assert resp["size"] == 50
        data = resp["items"]
        assert len(data) == 1

        assert data[0]["id"] == experience_config_privacy_center.id


class TestCreateExperienceConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + EXPERIENCE_CONFIG

    @pytest.fixture(scope="function")
    def overlay_banner_experience_request_body(self) -> dict:
        return {
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

    def test_create_experience_config_unauthenticated(self, url, api_client):
        resp = api_client.post(url)
        assert resp.status_code == 401

    def test_create_experience_config_wrong_scope(
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
    def test_create_experience_config_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
        overlay_banner_experience_request_body,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.post(
            url, json=overlay_banner_experience_request_body, headers=auth_header
        )
        assert response.status_code == expected_status

    def test_create_overlay_banner_experience_config_missing_banner_details(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "regions": ["eu_it", "eu_es", "eu_fr"],
                "component_title": "Manage your privacy",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "The following fields are required when defining a banner: ['banner_title', 'confirmation_button_label', 'reject_button_label']."
        )

    def test_create_experience_config_missing_link(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "privacy_center",
                "delivery_mechanism": "banner",
                "regions": ["eu_it", "eu_es", "eu_fr"],
                "component_title": "Manage your privacy",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Privacy center experiences can only be delivered via a link."
        )

        response = api_client.post(
            url,
            json={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "regions": ["eu_it", "eu_es", "eu_fr"],
                "component_title": "Manage your privacy",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Link label required when the delivery mechanism is of type link."
        )

    def test_create_experience_duplicate_regions(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "privacy_center",
                "delivery_mechanism": "banner",
                "regions": ["eu_it", "eu_it"],
                "component_title": "Manage your privacy",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Duplicate regions found."

    def test_create_experience_config_with_no_regions(
        self, api_client: TestClient, url, generate_auth_header, db
    ) -> None:
        """Experience config can be defined without any regions specified. This is handy for defining default experiences

        No privacy experiences are affected here.  But ExperienceConfig and ExperienceConfigHistory records are created.
        """
        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "component_title": "Manage your privacy",
                "link_label": "Go to the privacy center",
                "regions": [],
            },
            headers=auth_header,
        )
        assert response.status_code == 201
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] is None
        assert resp["banner_description"] is None
        assert resp["component"] == "privacy_center"
        assert resp["component_title"] == "Manage your privacy"
        assert resp["component_description"] is None
        assert resp["confirmation_button_label"] is None
        assert resp["delivery_mechanism"] == "link"
        assert resp["link_label"] == "Go to the privacy center"
        assert resp["reject_button_label"] is None
        assert resp["regions"] == []
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert resp["version"] == 1.0
        experience_config = get_experience_config_or_error(db, resp["id"])
        assert experience_config.experiences.all() == []
        assert experience_config.histories.count() == 1
        history = experience_config.histories[0]
        assert history.version == 1.0
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.experience_config_id == experience_config.id

        assert response.json()["linked_regions"] == []
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

        history.delete(db)
        experience_config.delete(db)

    def test_create_experience_config_no_existing_experiences(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
    ) -> None:
        """
        Specifying a NY region to be used with the new ExperienceConfig will cause a NY PrivacyExperience to be created
        behind the scenes if one doesn't exist.
        """

        assert (
            PrivacyExperience.get_experience_by_component_and_region(
                db, PrivacyNoticeRegion.us_ny, ComponentType.overlay
            )
            is None
        )

        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "regions": ["us_ny"],
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            },
            headers=auth_header,
        )
        assert response.status_code == 201
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] == "Manage your consent"
        assert (
            resp["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert resp["component"] == "overlay"
        assert resp["component_title"] == "Control your privacy"
        assert (
            resp["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert resp["confirmation_button_label"] == "Accept all"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["link_label"] is None
        assert resp["reject_button_label"] == "Reject all"
        assert resp["regions"] == ["us_ny"]
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert resp["version"] == 1.0

        # Created Experience Config
        experience_config = get_experience_config_or_error(db, resp["id"])
        assert experience_config.histories.count() == 1

        # Created Experience Config History
        experience_config_history = experience_config.histories[0]
        assert experience_config_history.version == 1.0
        assert experience_config_history.component == ComponentType.overlay
        assert experience_config_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_config_history.experience_config_id == experience_config.id

        # Created Privacy Experience
        assert experience_config.experiences.count() == 1
        experience = experience_config.experiences[0]
        assert experience.region == PrivacyNoticeRegion.us_ny
        assert experience.component == ComponentType.overlay
        assert experience.delivery_mechanism == DeliveryMechanism.banner
        assert experience.disabled is False
        assert experience.version == 1.0
        assert experience.experience_config_id == experience_config.id
        assert experience.experience_config_history_id == experience_config_history.id

        # Created Experience History
        assert experience.histories.count() == 1
        experience_history = experience.histories[0]
        assert experience_history.region == PrivacyNoticeRegion.us_ny
        assert experience_history.component == ComponentType.overlay
        assert experience_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_history.disabled is False
        assert experience_history.version == 1.0
        assert experience_history.experience_config_id == experience_config.id
        assert (
            experience_history.experience_config_history_id
            == experience_config_history.id
        )
        assert experience_history.privacy_experience_id == experience.id

        experience_history.delete(db)
        experience.delete(db)
        experience_config_history.delete(db)
        experience_config.delete(db)

        assert response.json()["linked_regions"] == ["us_ny"]
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

    def test_create_experience_config_existing_experiences(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
    ) -> None:
        """
        Specifying a TX region to be used with the new ExperienceConfig can
        cause an existing TX PrivacyExperience to be linked to the current ExperienceConfig
        with its version bumped
        """

        privacy_experience = PrivacyExperience.create(
            db,
            data={
                "disabled": False,
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.banner,
                "region": PrivacyNoticeRegion.us_tx,
            },
        )

        assert privacy_experience.version == 1.0
        assert privacy_experience.histories.count() == 1.0
        assert privacy_experience.experience_config_id is None

        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "regions": ["us_tx"],
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            },
            headers=auth_header,
        )
        assert response.status_code == 201
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] == "Manage your consent"
        assert (
            resp["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert resp["component"] == "overlay"
        assert resp["component_title"] == "Control your privacy"
        assert (
            resp["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert resp["confirmation_button_label"] == "Accept all"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["link_label"] is None
        assert resp["reject_button_label"] == "Reject all"
        assert resp["regions"] == ["us_tx"]
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert resp["version"] == 1.0

        # Created Experience Config
        experience_config = get_experience_config_or_error(db, resp["id"])
        assert experience_config.histories.count() == 1

        # Created Experience Config History
        experience_config_history = experience_config.histories[0]
        assert experience_config_history.version == 1.0
        assert experience_config_history.component == ComponentType.overlay
        assert experience_config_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_config_history.experience_config_id == experience_config.id

        # Updated Privacy Experience - TX Privacy Experience automatically linked, and bumped to 2.0
        assert experience_config.experiences.count() == 1
        experience = experience_config.experiences[0]
        db.refresh(experience)
        assert (
            experience == privacy_experience
        )  # Linked experience is the same Texas experience from above
        assert experience.region == PrivacyNoticeRegion.us_tx
        assert experience.component == ComponentType.overlay
        assert experience.delivery_mechanism == DeliveryMechanism.banner
        assert experience.disabled is False
        assert experience.version == 2.0
        assert experience.experience_config_id == experience_config.id
        assert experience.experience_config_history_id == experience_config_history.id

        # Created Experience History - new version of Privacy Experience created due to config being linked
        assert experience.histories.count() == 2
        experience_history = experience.histories[-1]
        assert experience_history.region == PrivacyNoticeRegion.us_tx
        assert experience_history.component == ComponentType.overlay
        assert experience_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_history.disabled is False
        assert experience_history.version == 2.0
        assert experience_history.experience_config_id == experience_config.id
        assert (
            experience_history.experience_config_history_id
            == experience_config_history.id
        )
        assert experience_history.privacy_experience_id == experience.id

        assert response.json()["linked_regions"] == ["us_tx"]
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

        for history in experience.histories:
            history.delete(db)
        experience.delete(db)
        experience_config_history.delete(db)
        experience_config.delete(db)

    def test_opt_in_notices_must_be_delivered_via_banner(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
    ) -> None:
        """
        Attempt to create an ExperienceConfig and link a region to that Experience that has notices
        that must be delivered in a different way. This fails because Texas cannot be linked here.
        """

        # Create an opt in notice that needs to be displayed in an overlay
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test Notice",
                "regions": [PrivacyNoticeRegion.us_tx],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["provide"],
                "enforcement_level": EnforcementLevel.frontend,
                "displayed_in_overlay": True,
            },
        )

        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_EXPERIENCE_CREATE, scopes.PRIVACY_EXPERIENCE_UPDATE]
        )
        response = api_client.post(
            url,
            json={
                "component": "overlay",
                "delivery_mechanism": "link",
                "regions": ["us_tx"],
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "link_label": "Manage your privacy here",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "The following regions would be incompatible with this experience: us_tx."
        )
        overlay_exp, banner_exp = PrivacyExperience.get_experiences_by_region(
            db, PrivacyNoticeRegion.us_tx
        )
        assert overlay_exp is None
        assert banner_exp is None

        privacy_notice.histories[0].delete(db)
        privacy_notice.delete(db)


class TestGetExperienceConfigDetail:
    @pytest.fixture(scope="function")
    def url(self, experience_config_overlay_banner) -> str:
        return (
            V1_URL_PREFIX
            + EXPERIENCE_CONFIG
            + f"/{experience_config_overlay_banner.id}"
        )

    def test_get_experience_config_detail_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_experience_config_detail_wrong_scope(
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
    def test_get_experience_config_detail_with_roles(
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

    @pytest.mark.usefixtures(
        "privacy_experience_overlay_banner",
    )
    def test_get_bad_experience_config_detail(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        url = V1_URL_PREFIX + EXPERIENCE_CONFIG + "/bad_id"

        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "No PrivacyExperienceConfig found for id 'bad_id'."
        )

    @pytest.mark.usefixtures(
        "privacy_experience_overlay_banner",
    )
    def test_get_experience_config_detail(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        experience_config_overlay_banner,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()

        assert resp["id"] == experience_config_overlay_banner.id
        assert resp["component"] == "overlay"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["disabled"] is True
        assert resp["regions"] == ["us_ca"]
        assert resp["version"] == 1.0
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert (
            resp["experience_config_history_id"]
            == experience_config_overlay_banner.experience_config_history_id
        )
        assert resp["banner_title"] == "Manage your consent"


class TestUpdateExperienceConfig:
    @pytest.fixture(scope="function")
    def url(self, overlay_banner_experience_config) -> str:
        return (
            V1_URL_PREFIX
            + EXPERIENCE_CONFIG
            + f"/{overlay_banner_experience_config.id}"
        )

    @pytest.fixture(scope="function")
    def overlay_banner_experience_config(self, db) -> PrivacyExperienceConfig:
        exp = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            },
        )
        yield exp
        for history in exp.histories:
            history.delete(db)
        exp.delete(db)

    def test_update_experience_config_unauthenticated(self, url, api_client):
        resp = api_client.patch(url, json={"disabled": True})
        assert resp.status_code == 401

    def test_update_experience_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])
        resp = api_client.patch(
            url,
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
    def test_update_experience_config_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.patch(
            url, json={"disabled": True, "regions": []}, headers=auth_header
        )
        assert response.status_code == expected_status

    def test_update_experience_config_duplicate_regions(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        """Failing if duplicate regions in request"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={"banner_title": None, "regions": ["us_ca", "us_ca"]},
            headers=auth_header,
        )
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Duplicate regions found."

    def test_update_bad_experience_config(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        """Nonexistent experience config id"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            V1_URL_PREFIX + EXPERIENCE_CONFIG + "/bad_experience_id",
            json={"banner_title": None, "regions": ["us_ca"]},
            headers=auth_header,
        )
        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "No PrivacyExperienceConfig found for id 'bad_experience_id'."
        )

    def test_update_overlay_banner_experience_config_missing_banner_details(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        """ExperienceConfig is currently for a banner, and we're trying to remove the banner title"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={"banner_title": None, "regions": []},
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "The following fields are required when defining a banner: ['banner_title', 'confirmation_button_label', 'reject_button_label']."
        )

    #
    def test_update_experience_config_missing_link(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        """ExperienceConfig is currently for a banner, and we're trying to convert it to a link here without all the necessary pieces"""
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={
                "delivery_mechanism": "link",
                "regions": [],
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Link label required when the delivery mechanism is of type link."
        )

    def test_update_experience_config_with_no_regions(
        self, api_client: TestClient, url, generate_auth_header, db
    ) -> None:
        """Test scenario where experience config has no regions and we make updates without any regions being
        involved.  Specifically disabling the ExperienceConfig
        """
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={
                "disabled": True,
                "regions": [],
            },
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] == "Manage your consent"
        assert (
            resp["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert resp["component"] == "overlay"
        assert resp["component_title"] == "Control your privacy"
        assert (
            resp["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert resp["confirmation_button_label"] == "Accept all"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["link_label"] is None
        assert resp["reject_button_label"] == "Reject all"
        assert resp["regions"] == []
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert resp["disabled"] is True
        assert resp["version"] == 2.0

        experience_config = get_experience_config_or_error(db, resp["id"])
        assert experience_config.experiences.all() == []
        assert experience_config.histories.count() == 2
        history = experience_config.histories[0]
        assert history.version == 1.0
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.experience_config_id == experience_config.id
        assert history.disabled is False

        history = experience_config.histories[1]
        assert history.version == 2.0
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.experience_config_id == experience_config.id
        assert history.disabled is True

        assert response.json()["linked_regions"] == []
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

        for history in experience_config.histories:
            history.delete(db)
        experience_config.delete(db)

    def test_update_experience_config_no_existing_experiences(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
        overlay_banner_experience_config,
    ) -> None:
        """
        This action is updating an existing ExperienceConfig to add NY.  NY does not have a PrivacyExperience
        yet, so one will be created for it.
        """

        assert (
            PrivacyExperience.get_experience_by_component_and_region(
                db, PrivacyNoticeRegion.us_ny, ComponentType.overlay
            )
            is None
        )

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={"regions": ["us_ny"]},
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] == "Manage your consent"
        assert (
            resp["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert resp["component"] == "overlay"
        assert resp["component_title"] == "Control your privacy"
        assert (
            resp["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert resp["confirmation_button_label"] == "Accept all"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["link_label"] is None
        assert resp["reject_button_label"] == "Reject all"
        assert resp["regions"] == ["us_ny"]
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert resp["version"] == 1.0
        assert resp["regions"] == ["us_ny"]

        # ExperienceConfig specifically wasn't updated, as this change is only changing which regions link here as FK
        db.refresh(overlay_banner_experience_config)
        assert overlay_banner_experience_config.id == resp["id"]
        assert overlay_banner_experience_config.histories.count() == 1

        # Existing Experience Config History
        experience_config_history = overlay_banner_experience_config.histories[0]
        assert experience_config_history.version == 1.0
        assert experience_config_history.component == ComponentType.overlay
        assert experience_config_history.delivery_mechanism == DeliveryMechanism.banner
        assert (
            experience_config_history.experience_config_id
            == overlay_banner_experience_config.id
        )

        # Created Privacy Experience
        assert overlay_banner_experience_config.experiences.count() == 1
        experience = overlay_banner_experience_config.experiences[0]
        assert experience.region == PrivacyNoticeRegion.us_ny
        assert experience.component == ComponentType.overlay
        assert experience.delivery_mechanism == DeliveryMechanism.banner
        assert experience.disabled is False
        assert experience.version == 1.0
        assert experience.experience_config_id == overlay_banner_experience_config.id
        assert experience.experience_config_history_id == experience_config_history.id

        # Created Experience History
        assert experience.histories.count() == 1
        experience_history = experience.histories[0]
        assert experience_history.region == PrivacyNoticeRegion.us_ny
        assert experience_history.component == ComponentType.overlay
        assert experience_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_history.disabled is False
        assert experience_history.version == 1.0
        assert (
            experience_history.experience_config_id
            == overlay_banner_experience_config.id
        )
        assert (
            experience_history.experience_config_history_id
            == experience_config_history.id
        )
        assert experience_history.privacy_experience_id == experience.id

        experience_history.delete(db)
        experience.delete(db)

        assert response.json()["linked_regions"] == ["us_ny"]
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

    def test_update_experience_config_regions_to_overlap_on_existing_experiences(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
        overlay_banner_experience_config,
    ) -> None:
        """
        Existing ExperienceConfig is updated to add TX.  A Texas Privacy Experience already exists.

        This should cause the existing Texas PrivacyExperience to be given a FK to the existing ExperienceConfig record
        with its version bumped as its config has changed.
        """

        privacy_experience = PrivacyExperience.create(
            db,
            data={
                "disabled": False,
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.banner,
                "region": PrivacyNoticeRegion.us_tx,
            },
        )

        assert privacy_experience.version == 1.0
        assert privacy_experience.histories.count() == 1.0
        assert privacy_experience.experience_config_id is None

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={
                "regions": ["us_tx"],
            },
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] == "Manage your consent"
        assert (
            resp["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert resp["component"] == "overlay"
        assert resp["component_title"] == "Control your privacy"
        assert (
            resp["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert resp["confirmation_button_label"] == "Accept all"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["link_label"] is None
        assert resp["reject_button_label"] == "Reject all"
        assert resp["regions"] == ["us_tx"]
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert (
            resp["version"] == 1.0
        ), "Version not bumped because config didn't change on ExperienceConfig"

        db.refresh(overlay_banner_experience_config)
        # Existing Experience Config History - no new version needed to be created
        assert overlay_banner_experience_config.histories.count() == 1
        experience_config_history = overlay_banner_experience_config.histories[0]
        assert experience_config_history.version == 1.0
        assert experience_config_history.component == ComponentType.overlay
        assert experience_config_history.delivery_mechanism == DeliveryMechanism.banner
        assert (
            experience_config_history.experience_config_id
            == overlay_banner_experience_config.id
        )

        # Updated Privacy Experience - TX Privacy Experience automatically linked, and bumped to 2.0
        assert overlay_banner_experience_config.experiences.count() == 1
        experience = overlay_banner_experience_config.experiences[0]
        db.refresh(experience)
        assert (
            experience == privacy_experience
        )  # Linked experience is the same Texas experience from above
        assert experience.region == PrivacyNoticeRegion.us_tx
        assert experience.component == ComponentType.overlay
        assert experience.delivery_mechanism == DeliveryMechanism.banner
        assert experience.disabled is False
        assert experience.version == 2.0
        assert experience.experience_config_id == overlay_banner_experience_config.id
        assert experience.experience_config_history_id == experience_config_history.id

        # Created Experience History - new version of Privacy Experience created due to config being linked
        assert experience.histories.count() == 2
        experience_history = experience.histories[-1]
        assert experience_history.region == PrivacyNoticeRegion.us_tx
        assert experience_history.component == ComponentType.overlay
        assert experience_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_history.disabled is False
        assert experience_history.version == 2.0
        assert (
            experience_history.experience_config_id
            == overlay_banner_experience_config.id
        )
        assert (
            experience_history.experience_config_history_id
            == experience_config_history.id
        )
        assert experience_history.privacy_experience_id == experience.id

        assert response.json()["linked_regions"] == ["us_tx"]
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

        for history in experience.histories:
            history.delete(db)
        experience.delete(db)

    def test_update_experience_config_experience_also_updated(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
        overlay_banner_experience_config,
    ) -> None:
        """
        Verify that if the ExperienceConfig is updated, some of those updates are passed onto the PrivacyExperience record.

        Existing ExperienceConfig is updated to add TX.  A Texas Privacy Experience already exists.
        We are updating the existing ExperienceConfig simultaneously. So the TX PrivacyExperience will
        be linked to the ExperienceConfig and also have select attributes from ExperienceConfig propagated back
        """

        privacy_experience = PrivacyExperience.create(
            db,
            data={
                "disabled": False,
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.banner,
                "region": PrivacyNoticeRegion.us_tx,
            },
        )

        assert privacy_experience.version == 1.0
        assert privacy_experience.histories.count() == 1.0
        assert privacy_experience.experience_config_id is None

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={"regions": ["us_tx"], "disabled": True},
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] is None
        assert resp["banner_title"] == "Manage your consent"
        assert (
            resp["banner_description"]
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert resp["component"] == "overlay"
        assert resp["component_title"] == "Control your privacy"
        assert (
            resp["component_description"]
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert resp["confirmation_button_label"] == "Accept all"
        assert resp["delivery_mechanism"] == "banner"
        assert resp["link_label"] is None
        assert resp["reject_button_label"] == "Reject all"
        assert resp["regions"] == ["us_tx"]
        assert resp["created_at"] is not None
        assert resp["updated_at"] is not None
        assert resp["disabled"] is True
        assert (
            resp["version"] == 2.0
        ), "Version bumped because we've disabled ExperienceConfig"

        db.refresh(overlay_banner_experience_config)
        # ExperienceConfig was disabled - this is a change, so another historical record is created
        assert overlay_banner_experience_config.histories.count() == 2
        experience_config_history = overlay_banner_experience_config.histories[1]
        assert experience_config_history.version == 2.0
        assert experience_config_history.disabled
        assert experience_config_history.component == ComponentType.overlay
        assert experience_config_history.delivery_mechanism == DeliveryMechanism.banner
        assert (
            experience_config_history.experience_config_id
            == overlay_banner_experience_config.id
        )

        # Updated Privacy Experience - TX Privacy Experience automatically linked, and bumped to 2.0
        assert overlay_banner_experience_config.experiences.count() == 1
        experience = overlay_banner_experience_config.experiences[0]
        db.refresh(experience)
        assert (
            experience == privacy_experience
        )  # Linked experience is the same Texas experience from above
        assert experience.region == PrivacyNoticeRegion.us_tx
        assert experience.component == ComponentType.overlay
        assert experience.delivery_mechanism == DeliveryMechanism.banner
        assert (
            experience.disabled is True
        ), "Experience disabled because it was linked to a disabled config"
        assert experience.version == 2.0
        assert experience.experience_config_id == overlay_banner_experience_config.id
        assert experience.experience_config_history_id == experience_config_history.id

        # Created Experience History - new version of Privacy Experience created due to config being linked
        assert experience.histories.count() == 2
        experience_history = experience.histories[-1]
        assert experience_history.region == PrivacyNoticeRegion.us_tx
        assert experience_history.component == ComponentType.overlay
        assert experience_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_history.disabled is True
        assert experience_history.version == 2.0
        assert (
            experience_history.experience_config_id
            == overlay_banner_experience_config.id
        )
        assert (
            experience_history.experience_config_history_id
            == experience_config_history.id
        )
        assert experience_history.privacy_experience_id == experience.id

        assert response.json()["linked_regions"] == ["us_tx"]
        assert response.json()["unlinked_regions"] == []
        assert response.json()["skipped_regions"] == []

        for history in experience.histories:
            history.delete(db)
        experience.delete(db)

    def test_update_experience_config_to_remove_region(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
        overlay_banner_experience_config,
    ) -> None:
        """
        Update the ExperienceConfig to remove a region. Verify this unlinks the region.
        """

        privacy_experience = PrivacyExperience.create(
            db,
            data={
                "disabled": False,
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.banner,
                "region": PrivacyNoticeRegion.us_tx,
                "experience_config_id": overlay_banner_experience_config.id,
                "experience_config_history_id": overlay_banner_experience_config.experience_config_history_id,
            },
        )

        assert privacy_experience.version == 1.0
        assert privacy_experience.histories.count() == 1.0
        assert (
            privacy_experience.experience_config_id
            == overlay_banner_experience_config.id
        )

        db.refresh(overlay_banner_experience_config)
        assert overlay_banner_experience_config.experiences.all() == [
            privacy_experience
        ]

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={
                "regions": [],
            },
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()["experience_config"]

        assert (
            resp["version"] == 1.0
        ), "Version not bumped because config didn't change, only region removed"

        db.refresh(overlay_banner_experience_config)
        # ExperienceConfig was disabled - this is a change, so another historical record is created
        assert overlay_banner_experience_config.histories.count() == 1
        experience_config_history = overlay_banner_experience_config.histories[0]
        assert experience_config_history.version == 1.0
        assert experience_config_history.component == ComponentType.overlay
        assert experience_config_history.delivery_mechanism == DeliveryMechanism.banner
        assert (
            experience_config_history.experience_config_id
            == overlay_banner_experience_config.id
        )

        # Updated Privacy Experience - TX Privacy Experience automatically *unlinked*, and bumped to 2.0
        assert overlay_banner_experience_config.experiences.count() == 0
        db.refresh(privacy_experience)

        assert privacy_experience.version == 2.0
        assert privacy_experience.experience_config_id is None
        assert privacy_experience.experience_config_history_id is None

        # Created Experience History - new version of Privacy Experience created due to config being *unlinked*
        assert privacy_experience.histories.count() == 2
        experience_history = privacy_experience.histories[-1]
        assert experience_history.region == PrivacyNoticeRegion.us_tx
        assert experience_history.component == ComponentType.overlay
        assert experience_history.delivery_mechanism == DeliveryMechanism.banner
        assert experience_history.disabled is False
        assert experience_history.version == 2.0
        assert experience_history.experience_config_id is None
        assert experience_history.experience_config_history_id is None
        assert experience_history.privacy_experience_id == privacy_experience.id

        assert response.json()["linked_regions"] == []
        assert response.json()["unlinked_regions"] == ["us_tx"]
        assert response.json()["skipped_regions"] == []

        for history in privacy_experience.histories:
            history.delete(db)
        privacy_experience.delete(db)

    def test_opt_in_notices_must_be_delivered_via_banner_not_already_linked(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
        overlay_banner_experience_config,
    ) -> None:
        """
        Attempt to update an ExperienceConfig and link a region to that Experience that has notices
        that must be delivered in a different way. The ExperienceConfig should be updated, but the conflicting
        region should not be linked
        """

        # Create an opt in notice that needs to be displayed in an overlay
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test Notice",
                "regions": [PrivacyNoticeRegion.us_tx],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["provide"],
                "enforcement_level": EnforcementLevel.frontend,
                "displayed_in_overlay": True,
            },
        )

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={
                "delivery_mechanism": "link",
                "regions": ["us_tx"],
                "link_label": "Manage your privacy here",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "The following regions would be incompatible with this experience: us_tx."
        )
        overlay_exp, banner_exp = PrivacyExperience.get_experiences_by_region(
            db, PrivacyNoticeRegion.us_tx
        )
        assert overlay_exp is None
        assert banner_exp is None

        db.refresh(overlay_banner_experience_config)
        assert overlay_banner_experience_config.experiences.count() == 0
        assert (
            overlay_banner_experience_config.delivery_mechanism
            == DeliveryMechanism.banner
        )

        privacy_notice.histories[0].delete(db)
        privacy_notice.delete(db)

    def test_opt_in_notices_must_be_delivered_via_banner_already_linked(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        db,
        overlay_banner_experience_config,
    ) -> None:
        """
        Attempt to update an ExperienceConfig that already has an Experience attached that needs to be delivered via
        banner, and this update would make it be delivered via link. Unlink the Experience.
        """

        # Create an opt in notice that needs to be displayed in an overlay
        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test Notice",
                "regions": [PrivacyNoticeRegion.us_tx],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["provide"],
                "enforcement_level": EnforcementLevel.frontend,
                "displayed_in_overlay": True,
            },
        )

        overlay_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "region": "us_tx",
                "experience_config_id": overlay_banner_experience_config.id,
                "experience_config_history_id": overlay_banner_experience_config.histories[
                    0
                ].id,
            },
        )

        assert overlay_banner_experience_config.experiences.all() == [overlay_exp]

        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_UPDATE])
        response = api_client.patch(
            url,
            json={
                "delivery_mechanism": "link",
                "regions": ["us_tx"],
                "link_label": "Manage your privacy here",
            },
            headers=auth_header,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "The following regions would be incompatible with this experience: us_tx."
        )
        overlay_exp, banner_exp = PrivacyExperience.get_experiences_by_region(
            db, PrivacyNoticeRegion.us_tx
        )
        assert overlay_exp == overlay_exp
        assert banner_exp is None

        db.refresh(overlay_banner_experience_config)
        assert overlay_banner_experience_config.experiences.count() == 1
        assert (
            overlay_banner_experience_config.delivery_mechanism
            == DeliveryMechanism.banner
        )

        overlay_exp.histories[0].delete(db)
        overlay_exp.delete(db)

        privacy_notice.histories[0].delete(db)
        privacy_notice.delete(db)
