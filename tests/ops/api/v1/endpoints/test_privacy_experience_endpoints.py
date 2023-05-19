from __future__ import annotations

import pytest
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.api.v1 import scope_registry as scopes
from fides.api.api.v1.urn_registry import (
    PRIVACY_EXPERIENCE,
    PRIVACY_EXPERIENCE_DETAIL,
    V1_URL_PREFIX,
)


class TestGetPrivacyExperiences:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_EXPERIENCE

    def test_get_privacy_experiences_unauthenticated(self, url, api_client):
        """This is a public endpoint"""
        resp = api_client.get(url)
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_200_OK),
            ("viewer", HTTP_200_OK),
            ("approver", HTTP_200_OK),
        ],
    )
    def test_get_privacy_experience_with_roles(
        self, role, expected_status, api_client: TestClient, url, generate_role_header
    ) -> None:
        """This is a public endpoint"""
        auth_header = generate_role_header(roles=[role])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == expected_status

    def test_get_privacy_experiences(
        self,
        api_client: TestClient,
        url,
        privacy_notice,
        privacy_experience_privacy_center_link,
    ):
        resp = api_client.get(
            url,
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
        assert resp["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert resp["privacy_notices"][0]["default_preference"] == "opt_out"
        assert resp["privacy_notices"][0]["current_preference"] is None
        assert resp["privacy_notices"][0]["outdated_preference"] is None

    def test_get_privacy_experiences_show_disabled_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
    ):
        resp = api_client.get(
            url,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

        resp = api_client.get(
            url + "?show_disabled=False",
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

    @pytest.mark.usefixtures(
        "privacy_experience_privacy_center_link",
    )
    def test_get_privacy_experiences_region_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
    ):
        resp = api_client.get(
            url + "?region=eu_fr",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == privacy_experience_overlay_link.id
        assert data["items"][0]["region"] == "eu_fr"
        resp = api_client.get(
            url + "?region=us_ca",
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
        )
        assert resp.status_code == 422

        resp = api_client.get(
            url + "?region=eu_it",
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_get_privacy_experiences_components_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
    ):
        resp = api_client.get(
            url + "?component=overlay",
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
        )
        assert resp.status_code == 422

    @pytest.mark.usefixtures(
        "privacy_experience_privacy_center_link",
        "privacy_experience_overlay_link",
        "privacy_experience_overlay_banner",
    )
    def test_get_privacy_experiences_has_notices_no_notices(
        self, api_client: TestClient, url
    ):
        resp = api_client.get(
            url + "?has_notices=True",
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
        self, api_client: TestClient, url
    ):
        resp = api_client.get(
            url + "?has_notices=True",
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
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
        privacy_notice_eu_fr_provide_service_frontend_only,
        privacy_notice_us_ca_provide,
    ):
        resp = api_client.get(
            url + "?has_notices=True",
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
        url,
        privacy_experience_privacy_center_link,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
    ):
        """Region filter propagates through to the notices too"""
        resp = api_client.get(
            url + "?has_notices=True&region=us_co",
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
        db,
        url,
        privacy_experience_privacy_center_link,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
    ):
        """Region filter propagates through to the notices too"""
        privacy_notice_us_co_third_party_sharing.disabled = True
        privacy_notice_us_co_third_party_sharing.save(db)

        resp = api_client.get(
            url + "?has_notices=True&region=us_co&show_disabled=False",
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

    def test_get_privacy_experiences_show_has_config_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_experience_privacy_center_link,
        privacy_experience_overlay_link,
        privacy_experience_overlay_banner,
        db,
    ):
        resp = api_client.get(
            url + "?has_config=False",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

        resp = api_client.get(
            url + "?has_config=True",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert {config["id"] for config in data["items"]} == {
            privacy_experience_privacy_center_link.id,
            privacy_experience_overlay_link.id,
            privacy_experience_overlay_banner.id,
        }

        privacy_experience_privacy_center_link.experience_config_id = None
        privacy_experience_privacy_center_link.experience_config_history_id = None

        privacy_experience_privacy_center_link.save(db=db)
        resp = api_client.get(
            url + "?has_config=False",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == privacy_experience_privacy_center_link.id

    @pytest.mark.usefixtures(
        "privacy_notice_us_ca_provide",
        "fides_user_provided_identity",
        "privacy_preference_history_us_ca_provide_for_fides_user",
        "privacy_experience_overlay_banner",
    )
    def test_get_privacy_experiences_fides_user_device_id_filter(
        self,
        api_client: TestClient,
        url,
    ):
        resp = api_client.get(
            url + "?fides_user_device_id=FGHIJ_TEST_FIDES",
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert one experience in the response
        assert data["total"] == 1
        assert len(data["items"]) == 1
        resp = data["items"][0]

        # Assert current preference is displayed for fides user device id
        assert resp["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert resp["privacy_notices"][0]["default_preference"] == "opt_out"
        assert resp["privacy_notices"][0]["current_preference"] == "opt_in"
        assert resp["privacy_notices"][0]["outdated_preference"] is None


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
        assert experience_config["acknowledgement_button_label"] == "Confirm"
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

        # Assert default preferences displayed only
        assert body["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert body["privacy_notices"][0]["default_preference"] == "opt_out"
        assert body["privacy_notices"][0]["current_preference"] is None
        assert body["privacy_notices"][0]["outdated_preference"] is None

        # Assert default preferences displayed only
        assert body["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert body["privacy_notices"][0]["default_preference"] == "opt_out"
        assert body["privacy_notices"][0]["current_preference"] is None
        assert body["privacy_notices"][0]["outdated_preference"] is None

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

    @pytest.mark.usefixtures(
        "privacy_notice_us_ca_provide",
        "fides_user_provided_identity",
        "privacy_preference_history_us_ca_provide_for_fides_user",
        "privacy_experience_overlay_banner",
    )
    def test_get_privacy_experience_detail_fides_user_device_id_filter(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[scopes.PRIVACY_EXPERIENCE_READ])

        resp = api_client.get(
            url + "?fides_user_device_id=FGHIJ_TEST_FIDES",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Assert current preference is displayed for fides user device id
        assert data["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert data["privacy_notices"][0]["default_preference"] == "opt_out"
        assert data["privacy_notices"][0]["current_preference"] == "opt_in"
        assert data["privacy_notices"][0]["outdated_preference"] is None
