import json

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.api.models.sql_models import DataUse
from fides.common.api.scope_registry import DATA_USE, DATA_USE_CREATE, STORAGE_READ
from fides.common.api.v1.urn_registry import V1_URL_PREFIX


class TestCreateDataUse:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + "/" + DATA_USE

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "name": "test data use",
            "description": "this is a test data use",
            "is_default": False,
        }

    @pytest.fixture(scope="function")
    def disabled_data_use(self, db: Session):
        payload = {
            "name": "test data use",
            "fides_key": "test_data_use",
            "active": False,
            "is_default": False,
            "description": "Disabled data use",
        }
        dataUse = DataUse.create(db=db, data=payload)
        yield dataUse
        dataUse.delete(db)

    @pytest.fixture(scope="function")
    def enabled_data_use(self, db: Session):
        payload = {
            "name": "test data use",
            "fides_key": "test_data_use",
            "active": True,
            "is_default": False,
            "description": "Disabled data use",
        }
        dataUse = DataUse.create(db=db, data=payload)
        yield dataUse
        dataUse.delete(db)

    def test_create_data_use_not_authenticated(
        self,
        api_client: TestClient,
        payload,
        url,
    ):
        response = api_client.post(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_create_data_use_incorrect_scope(
        self,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_create_data_use_with_fides_key_and_parent_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_CREATE])
        payload["fides_key"] = "analytics.test_data_use"
        payload["parent_key"] = "analytics"
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 201 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["fides_key"] == "analytics.test_data_use"
        data_use = db.query(DataUse).filter_by(fides_key="analytics.test_data_use")[0]
        data_use.delete(db)

    def test_create_data_use_with_fides_key_and_non_matching_parent_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        payload["fides_key"] = "analytics.test_data_use"
        payload["parent_key"] = "invalid_parent"
        auth_header = generate_auth_header([DATA_USE_CREATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 422 == response.status_code

    def test_create_data_use_with_no_fides_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_CREATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 201 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["fides_key"] == "test_data_use"
        data_use = db.query(DataUse).filter_by(fides_key="test_data_use")[0]
        data_use.delete(db)

    def test_create_data_use_with_no_fides_key_and_has_parent_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_CREATE])
        payload["parent_key"] = "analytics"
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 201 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["fides_key"] == "analytics.test_data_use"
        data_use = db.query(DataUse).filter_by(fides_key="analytics.test_data_use")[0]
        data_use.delete(db)

    def test_create_data_use_with_conflicting_key(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        enabled_data_use,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_CREATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 422 == response.status_code

    def test_create_data_use_with_disabled_matching_name(
        self,
        db: Session,
        api_client: TestClient,
        payload,
        url,
        disabled_data_use,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_CREATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 201 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["fides_key"] == "test_data_use"
        assert response_body["description"] == "this is a test data use"
        data_use = db.query(DataUse).filter_by(fides_key="test_data_use")[0]
        data_use.delete(db)
