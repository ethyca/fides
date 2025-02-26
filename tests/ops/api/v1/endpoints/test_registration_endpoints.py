from unittest import mock

import pytest

from fides.api.models.registration import UserRegistration
from fides.common.api.v1.urn_registry import REGISTRATION, V1_URL_PREFIX


class TestUserRegistrationModel:

    def test_registration_as_log(self, db):
        EXAMPLE_ANALYTICS_ID = "example-analytics-id"
        OPT_IN = True

        user_reg = UserRegistration.create(
            db,
            data={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "analytics_id": EXAMPLE_ANALYTICS_ID,
                "opt_in": OPT_IN,
            },
        )

        fideslog_reg = user_reg.as_fideslog()
        assert fideslog_reg.organization == "Example Org."


class TestUserRegistration:
    """Tests for the UserRegistration API, configured during `fides deploy`."""

    @pytest.fixture(scope="session")
    def url(self) -> str:
        return V1_URL_PREFIX + REGISTRATION

    def test_get_registration_unregistered(
        self,
        url,
        api_client,
        db,
    ):
        assert len(UserRegistration.all(db)) == 0

        resp = api_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["opt_in"] == False

    def test_get_registration_opt_out(
        self,
        url,
        api_client,
        user_registration_opt_out,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["opt_in"] == False

    def test_get_registration_opt_in(
        self,
        url,
        api_client,
        user_registration_opt_in,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["opt_in"] == True

    @mock.patch("fides.api.api.v1.endpoints.registration_endpoints.send_registration")
    def test_register_user(
        self,
        send_registration_mock,
        url,
        api_client,
        db,
    ):
        assert len(UserRegistration.all(db)) == 0
        EXAMPLE_ANALYTICS_ID = "example-analytics-id"
        OPT_IN = True
        resp = api_client.put(
            url,
            json={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "analytics_id": EXAMPLE_ANALYTICS_ID,
                "opt_in": OPT_IN,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analytics_id"] == EXAMPLE_ANALYTICS_ID
        assert data["opt_in"] == OPT_IN
        assert len(UserRegistration.all(db)) == 1
        assert send_registration_mock.call_count == 1

    @mock.patch("fides.api.api.v1.endpoints.registration_endpoints.send_registration")
    def test_register_user_upserts_locally(
        self,
        send_registration_mock,
        url,
        api_client,
        db,
        user_registration_opt_out,
    ):
        resp = api_client.put(
            url,
            json={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "analytics_id": user_registration_opt_out.analytics_id,
                "opt_in": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analytics_id"] == user_registration_opt_out.analytics_id
        assert data["opt_in"] == True
        assert len(UserRegistration.all(db)) == 1
        assert send_registration_mock.call_count == 0

    def test_register_user_no_analytics_id(
        self,
        url,
        api_client,
        db,
    ):
        resp = api_client.put(
            url,
            json={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "opt_in": True,
            },
        )
        assert resp.status_code == 422
        assert len(UserRegistration.all(db)) == 0

    @mock.patch("fides.api.api.v1.endpoints.registration_endpoints.send_registration")
    def test_register_user_one_allowed(
        self,
        send_registration_mock,
        url,
        api_client,
        db,
        user_registration_opt_out,
    ):
        resp = api_client.put(
            url,
            json={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "analytics_id": "another-analytics-id",
                "opt_in": True,
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "This Fides deployment is already registered."
        assert len(UserRegistration.all(db)) == 1
        assert not send_registration_mock.called
