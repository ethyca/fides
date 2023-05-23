from __future__ import annotations

import pytest
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.api.v1 import scope_registry as scopes
from fides.api.api.v1.endpoints.privacy_experience_config_endpoints import (
    get_experience_config_or_error,
)
from fides.api.api.v1.urn_registry import EXPERIENCE_CONFIG, V1_URL_PREFIX
from fides.api.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    PrivacyExperience,
    PrivacyExperienceConfig,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
)


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
            "acknowledgement_button_label": "Confirm",
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
            == "The following fields are required when defining a banner: ['acknowledgement_button_label', 'banner_title', 'confirmation_button_label', 'reject_button_label']."
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
            PrivacyExperience.get_experience_by_region_and_component(
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
                "acknowledgement_button_label": "Confirm",
            },
            headers=auth_header,
        )
        assert response.status_code == 201
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] == "Confirm"
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
                "acknowledgement_button_label": "Confirm",
            },
            headers=auth_header,
        )
        assert response.status_code == 201
        resp = response.json()["experience_config"]
        assert resp["acknowledgement_button_label"] == "Confirm"
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
                "notice_key": "test_notice",
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
            == "No Privacy Experience Config found for id 'bad_id'."
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
                "acknowledgement_button_label": "Confirm",
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
            == "No Privacy Experience Config found for id 'bad_experience_id'."
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
            == "The following fields are required when defining a banner: ['acknowledgement_button_label', 'banner_title', 'confirmation_button_label', 'reject_button_label']."
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
        assert resp["acknowledgement_button_label"] == "Confirm"
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
        assert resp["acknowledgement_button_label"] == "Confirm"
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
            PrivacyExperience.get_experience_by_region_and_component(
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
        assert resp["acknowledgement_button_label"] == "Confirm"
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
        assert resp["acknowledgement_button_label"] == "Confirm"
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
        assert resp["acknowledgement_button_label"] == "Confirm"
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
                "notice_key": "test_notice",
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
                "notice_key": "test_notice",
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
