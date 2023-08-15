from __future__ import annotations

import pytest
from starlette.status import HTTP_200_OK
from starlette.testclient import TestClient

from fides.api.models.privacy_notice import ConsentMechanism
from fides.common.api.v1.urn_registry import PRIVACY_EXPERIENCE, V1_URL_PREFIX


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
        privacy_experience_privacy_center,
    ):
        unescape_header = {"Unescape-Safestr": "true"}

        resp = api_client.get(url, headers=unescape_header)
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # assert one experience in the response
        assert data["total"] == 1
        assert len(data["items"]) == 1
        resp = data["items"][0]

        assert resp["component"] == "privacy_center"
        assert resp["region"] == "us_co"
        assert resp["show_banner"] is False
        # Assert experience config is nested
        experience_config = resp["experience_config"]
        assert experience_config["title"] == "Control your privacy"
        assert experience_config["description"] == "user's description <script />"
        assert experience_config["banner_enabled"] is None
        assert experience_config["accept_button_label"] == "Accept all"
        assert experience_config["reject_button_label"] == "Reject all"
        assert experience_config["acknowledge_button_label"] is None
        assert experience_config["id"] is not None
        assert experience_config["version"] == 1
        assert (
            experience_config["experience_config_history_id"]
            == privacy_experience_privacy_center.experience_config.experience_config_history_id
        )
        assert len(resp["privacy_notices"]) == 1
        assert resp["privacy_notices"][0]["id"] == privacy_notice.id
        assert resp["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert resp["privacy_notices"][0]["default_preference"] == "opt_out"
        assert resp["privacy_notices"][0]["current_preference"] is None
        assert resp["privacy_notices"][0]["outdated_preference"] is None
        assert (
            resp["privacy_notices"][0]["description"] == "user's description <script />"
        )

    def test_get_experiences_unescaped(
        self,
        api_client,
        url,
        privacy_notice,
        privacy_experience_privacy_center,
    ):
        # Assert not escaped without proper request header
        resp = api_client.get(url)
        resp = resp.json()["items"][0]
        experience_config = resp["experience_config"]
        assert (
            experience_config["description"]
            == "user&#x27;s description &lt;script /&gt;"
        )
        assert (
            resp["privacy_notices"][0]["description"]
            == "user&#x27;s description &lt;script /&gt;"
        )

    def test_get_privacy_experiences_show_disabled_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
        privacy_experience_overlay,
        db,
    ):
        resp = api_client.get(
            url,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        resp = api_client.get(
            url + "?show_disabled=False",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_overlay.id,
        }

        assert privacy_experience_privacy_center.id not in {
            exp["id"] for exp in data["items"]
        }

        privacy_experience_overlay.unlink_experience_config(db)
        resp = api_client.get(
            url + "?show_disabled=False",
        )
        data = resp.json()
        assert (
            data["total"] == 0
        ), "Experience config was removed from experience so it is considered 'disabled' by default"
        assert len(data["items"]) == 0

    def test_get_privacy_experiences_region_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
        privacy_experience_overlay,
        privacy_notice_france,
        privacy_experience_privacy_center_france,
    ):
        resp = api_client.get(
            url + "?region=us_co",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == privacy_experience_privacy_center.id
        assert data["items"][0]["region"] == "us_co"

        resp = api_client.get(
            url + "?region=us_ca",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_overlay.id,
        }
        assert data["items"][0]["region"] == "us_ca"

        resp = api_client.get(
            url + "?region=bad_region",
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

        resp = api_client.get(
            url + "?region=fr_idg",
        )  # There are no experiences with "fr_idg" so we fell back to searching for "fr"
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        data = resp.json()
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_privacy_center_france.id
        }
        assert len(data["items"][0]["privacy_notices"]) == 1
        assert data["items"][0]["privacy_notices"][0]["regions"] == ["fr"]
        assert data["items"][0]["privacy_notices"][0]["id"] == privacy_notice_france.id

    def test_get_privacy_experiences_components_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
        privacy_experience_overlay,
    ):
        resp = api_client.get(
            url + "?component=overlay",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_overlay.id,
        }

        resp = api_client.get(
            url + "?component=privacy_center",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert {exp["id"] for exp in data["items"]} == {
            privacy_experience_privacy_center.id
        }

        resp = api_client.get(
            url + "?component=bad_type",
        )
        assert resp.status_code == 422

    @pytest.mark.usefixtures(
        "privacy_experience_privacy_center",
        "privacy_experience_overlay",
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
        "privacy_experience_privacy_center",
        "privacy_experience_overlay",
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
        "privacy_notice_fr_provide_service_frontend_only",
    )
    def test_get_privacy_experiences_has_notices(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
        privacy_experience_overlay,
        privacy_notice,
        privacy_notice_us_co_third_party_sharing,
        privacy_notice_us_ca_provide,
    ):
        resp = api_client.get(
            url + "?has_notices=True",
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

        first_experience = data["items"][0]
        assert (
            first_experience["id"] == privacy_experience_overlay.id
        )  # Most recently created
        assert first_experience["component"] == "overlay"
        assert first_experience["region"] == "us_ca"
        assert first_experience["show_banner"] is True
        assert len(first_experience["privacy_notices"]) == 2

        # Notices match on region and "overlay"
        privacy_experience_overlay_notice_1 = first_experience["privacy_notices"][0]
        assert (
            privacy_experience_overlay_notice_1["id"] == privacy_notice_us_ca_provide.id
        )
        assert privacy_experience_overlay_notice_1["regions"] == ["us_ca"]
        assert privacy_experience_overlay_notice_1["displayed_in_overlay"]
        assert (
            privacy_experience_overlay_notice_1["consent_mechanism"]
            == ConsentMechanism.opt_in.value
        )

        privacy_experience_overlay_notice_2 = first_experience["privacy_notices"][1]
        assert privacy_experience_overlay_notice_2["id"] == privacy_notice.id
        assert privacy_experience_overlay_notice_2["regions"] == ["us_ca", "us_co"]
        assert privacy_experience_overlay_notice_2["displayed_in_overlay"]

        second_experience = data["items"][1]
        assert (
            second_experience["id"] == privacy_experience_privacy_center.id
        )  # Most recently created
        assert second_experience["component"] == "privacy_center"
        assert second_experience["region"] == "us_co"
        assert second_experience["show_banner"] is False
        assert len(second_experience["privacy_notices"]) == 2

        # Notices match on region and "overlay"
        privacy_experience_privacy_center_notice_1 = second_experience[
            "privacy_notices"
        ][0]
        assert (
            privacy_experience_privacy_center_notice_1["id"]
            == privacy_notice_us_co_third_party_sharing.id
        )
        assert privacy_experience_privacy_center_notice_1["regions"] == ["us_co"]
        assert privacy_experience_privacy_center_notice_1["displayed_in_privacy_center"]

        privacy_experience_privacy_center_notice_2 = second_experience[
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
        "privacy_experience_overlay",  # us_ca
        "privacy_notice_fr_provide_service_frontend_only",  # fr
        "privacy_notice_us_ca_provide",  # us_ca
    )
    def test_filter_on_notices_and_region(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
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

        assert data["items"][0]["id"] == privacy_experience_privacy_center.id
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
        "privacy_experience_overlay",  # us_ca
        "privacy_notice_fr_provide_service_frontend_only",  # eu_fr
        "privacy_notice_us_ca_provide",  # us_ca
        "privacy_experience_privacy_center",
    )
    def test_filter_on_systems_applicable(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
        privacy_notice,
        system,
        privacy_notice_us_co_third_party_sharing,
    ):
        """For systems applicable filter, notices are only embedded if they are relevant to a system"""
        resp = api_client.get(
            url + "?region=us_co",
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1

        notices = data["items"][0]["privacy_notices"]
        assert len(notices) == 2
        assert notices[0]["regions"] == ["us_co"]
        assert notices[0]["id"] == privacy_notice_us_co_third_party_sharing.id
        assert notices[0]["displayed_in_privacy_center"]
        assert notices[0]["data_uses"] == ["third_party_sharing"]

        assert notices[1]["regions"] == ["us_ca", "us_co"]
        assert notices[1]["id"] == privacy_notice.id
        assert notices[1]["displayed_in_privacy_center"]
        assert notices[1]["data_uses"] == [
            "marketing.advertising",
            "third_party_sharing",
        ]

        resp = api_client.get(
            url + "?region=us_co&systems_applicable=True",
        )
        notices = resp.json()["items"][0]["privacy_notices"]
        assert len(notices) == 1
        assert notices[0]["regions"] == ["us_ca", "us_co"]
        assert notices[0]["id"] == privacy_notice.id
        assert notices[0]["displayed_in_privacy_center"]
        assert notices[0]["data_uses"] == [
            "marketing.advertising",
            "third_party_sharing",
        ]
        assert system.privacy_declarations[0].data_use == "marketing.advertising"

    @pytest.mark.usefixtures(
        "privacy_notice_us_co_provide_service_operations",  # not displayed in overlay or privacy center
        "privacy_notice_eu_cy_provide_service_frontend_only",  # doesn't overlap with any regions,
        "privacy_experience_privacy_center",
        "privacy_notice_fr_provide_service_frontend_only",  # fr
        "privacy_notice_us_co_third_party_sharing",  # us_co
    )
    def test_filter_on_notices_and_region_and_show_disabled_is_false(
        self,
        api_client: TestClient,
        db,
        url,
        privacy_experience_overlay,
        privacy_notice,
        privacy_notice_us_ca_provide,
    ):
        """Region filter propagates through to the notices too"""

        privacy_notice_us_ca_provide.disabled = True
        privacy_notice_us_ca_provide.save(db)

        resp = api_client.get(
            url + "?has_notices=True&region=us_ca&show_disabled=False",
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1

        assert data["items"][0]["id"] == privacy_experience_overlay.id
        assert data["items"][0]["region"] == "us_ca"

        notices = data["items"][0]["privacy_notices"]
        assert len(notices) == 1
        assert notices[0]["regions"] == ["us_ca", "us_co"]
        assert notices[0]["id"] == privacy_notice.id
        assert notices[0]["displayed_in_overlay"]

    def test_get_privacy_experiences_show_has_config_filter(
        self,
        api_client: TestClient,
        url,
        privacy_experience_privacy_center,
        privacy_experience_overlay,
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
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert {config["id"] for config in data["items"]} == {
            privacy_experience_privacy_center.id,
            privacy_experience_overlay.id,
        }

        privacy_experience_privacy_center.experience_config_id = None
        privacy_experience_privacy_center.experience_config_history_id = None

        privacy_experience_privacy_center.save(db=db)
        resp = api_client.get(
            url + "?has_config=False",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == privacy_experience_privacy_center.id

    def test_get_privacy_experiences_bad_fides_user_device_id_filter(
        self,
        api_client: TestClient,
        url,
    ):
        resp = api_client.get(
            url + "?fides_user_device_id=does_not_exist",
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == "Invalid fides user device id format"

    @pytest.mark.usefixtures(
        "privacy_notice_us_ca_provide",
        "fides_user_provided_identity",
        "privacy_preference_history_us_ca_provide_for_fides_user",
        "privacy_experience_overlay",
    )
    def test_get_privacy_experiences_nonexistent_fides_user_device_id_filter(
        self,
        api_client: TestClient,
        url,
    ):
        resp = api_client.get(
            url + "?cd685ccd-0960-4dc1-b9ca-7e810ebc5c1b",
        )
        assert resp.status_code == 200
        data = resp.json()
        resp = data["items"][0]

        # Assert current preference is displayed for fides user device id
        assert resp["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert resp["privacy_notices"][0]["default_preference"] == "opt_out"
        assert resp["privacy_notices"][0]["current_preference"] is None
        assert resp["privacy_notices"][0]["outdated_preference"] is None

        assert resp["privacy_notices"][0]["current_served"] is None
        assert resp["privacy_notices"][0]["outdated_served"] is None

    @pytest.mark.usefixtures(
        "privacy_notice_us_ca_provide",
        "fides_user_provided_identity",
        "privacy_preference_history_us_ca_provide_for_fides_user",
        "served_notice_history_us_ca_provide_for_fides_user",
        "privacy_experience_overlay",
    )
    def test_get_privacy_experiences_fides_user_device_id_filter(
        self, db, api_client: TestClient, url, privacy_notice_us_ca_provide
    ):
        resp = api_client.get(
            url + "?fides_user_device_id=051b219f-20e4-45df-82f7-5eb68a00889f",
        )
        assert resp.status_code == 200
        data = resp.json()["items"][0]
        assert data["show_banner"] is True

        # Assert current preference is displayed for fides user device id
        assert data["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert data["privacy_notices"][0]["default_preference"] == "opt_out"
        assert data["privacy_notices"][0]["current_preference"] == "opt_in"
        assert data["privacy_notices"][0]["outdated_preference"] is None
        # Assert that the notice was served is surfaced
        assert data["privacy_notices"][0]["current_served"] is True
        assert data["privacy_notices"][0]["outdated_served"] is None

        assert (
            data["privacy_notices"][0]["notice_key"]
            == "example_privacy_notice_us_ca_provide"
        )

        privacy_notice_us_ca_provide.update(db, data={"description": "new_description"})
        assert privacy_notice_us_ca_provide.version == 2.0
        assert privacy_notice_us_ca_provide.description == "new_description"
        resp = api_client.get(
            url + "?fides_user_device_id=051b219f-20e4-45df-82f7-5eb68a00889f",
        )
        assert resp.status_code == 200
        data = resp.json()["items"][0]
        # Assert outdated preference is displayed for fides user device id
        assert data["privacy_notices"][0]["consent_mechanism"] == "opt_in"
        assert data["privacy_notices"][0]["default_preference"] == "opt_out"
        assert data["privacy_notices"][0]["current_preference"] is None
        assert data["privacy_notices"][0]["outdated_preference"] == "opt_in"
        # Assert outdated served is displayed for fides user device id
        assert data["privacy_notices"][0]["current_served"] is None
        assert data["privacy_notices"][0]["outdated_served"] is True
