import json
from datetime import datetime, timedelta
from typing import List

import pytest


from fides.api.ops.api.v1.urn_registry import (
    V1_URL_PREFIX,
    REGISTRATION,
)
from fides.api.ops.models.registration import UserRegistration
from fides.ctl.core.config import get_config


class TestUserRegistration:
    """ """

    @pytest.fixture(scope="session")
    def url(self) -> str:
        return V1_URL_PREFIX + REGISTRATION

    def test_get_registration_uninstalled(
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

    def test_get_registration_unregistered(
        self,
        url,
        api_client,
        user_registration_unregistered,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["opt_in"] == False

    def test_get_registration_registered(
        self,
        url,
        api_client,
        user_registration_registered,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["opt_in"] == True

    def test_register_user(
        self,
        url,
        api_client,
        db,
    ):
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

    def test_register_user_upserts(
        self,
        url,
        api_client,
        db,
        user_registration_unregistered,
    ):
        resp = api_client.put(
            url,
            json={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "analytics_id": user_registration_unregistered.analytics_id,
                "opt_in": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analytics_id"] == user_registration_unregistered.analytics_id
        assert data["opt_in"] == True
        assert len(UserRegistration.all(db)) == 1

    def test_register_user_no_analytics_id(
        self,
        url,
        api_client,
        db,
        user_registration_unregistered,
    ):
        resp = api_client.put(
            url,
            json={
                "user_email": "user@example.com",
                "user_organization": "Example Org.",
                "opt_in": True,
            },
        )
        assert resp.status_code == 400
        assert (
            resp.json()["details"]
            == "Please supply an `analytics_id` to register Fides."
        )
        assert len(UserRegistration.all(db)) == 1

    def test_register_user_one_allowed(
        self,
        url,
        api_client,
        db,
        user_registration_unregistered,
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
        assert resp.json()["details"] == "This Fides deployment is already registered."
        assert len(UserRegistration.all(db)) == 1
