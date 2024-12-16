import json

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.api.models.sql_models import DataUse
from fides.common.api.scope_registry import DATA_USE, DATA_USE_CREATE, STORAGE_READ, DATA_USE_UPDATE
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
    def deactive_data_use(self, db: Session):
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
    def active_data_use(self, db: Session):
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
        active_data_use,
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
        deactive_data_use,
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


class TestUpdateDataUse:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + "/" + DATA_USE

    @pytest.fixture(scope="function")
    def payload(self):
        return {
            "fides_key": "test_data_use",
            "name": "test data use",
            "description": "this is a test data use",
            "is_default": False,
        }

    @pytest.fixture(scope="function")
    def data_use(self, db: Session):
        payload = {
            "name": "test data use",
            "fides_key": "test_data_use",
            "active": False,
            "is_default": False,
            "description": "De-active data use",
        }
        dataUse = DataUse.create(db=db, data=payload)
        yield dataUse
        dataUse.delete(db)

    def test_update_data_use_not_authenticated(
            self,
            api_client: TestClient,
            data_use,
            payload,
            url,
    ):
        response = api_client.put(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_update_data_use_incorrect_scope(
            self,
            api_client: TestClient,
            payload,
            data_use,
            url,
            generate_auth_header,
    ):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_update_data_use_not_found(
            self,
            db: Session,
            api_client: TestClient,
            payload,
            data_use,
            url,
            generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_UPDATE])
        payload["fides_key"] = "does_not_exist"
        response = api_client.put(url, headers=auth_header, json=payload)

        assert 404 == response.status_code

    def test_update_data_use_name_and_description(
            self,
            api_client: TestClient,
            payload,
            data_use,
            url,
            generate_auth_header,
    ):
        auth_header = generate_auth_header([DATA_USE_UPDATE])
        payload["name"] = "New name"
        payload["description"] = "New description"
        response = api_client.put(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)

        assert response_body["name"] == "New name"
        assert response_body["description"] == "New description"

    def test_update_data_use_activate_propagates_up(
            self,
            db: Session,
            api_client: TestClient,
            url,
            generate_auth_header,
    ):
        """
        Tree: A----B----C
                   \
                    ----D
        Current Active Fields: A (true), B (false), C (false), D (false)
        Payload: C: active=True
        Result Active Fields: A (true), B (true), C (true), D (false)
        """
        # Set up Current Taxonomy Tree
        payload_a = {
            "name": "Data Use A",
            "fides_key": "data_use_a",
            "active": True,
            "is_default": False,
            "description": "Data Use A",
        }
        payload_b = {
            "name": "Data Use B",
            "fides_key": "data_use_b",
            "active": False,
            "is_default": False,
            "description": "Data Use B",
        }
        payload_c = {
            "name": "Data Use C",
            "fides_key": "data_use_c",
            "active": False,
            "is_default": False,
            "description": "Data Use C",
        }
        payload_d = {
            "name": "Data Use D",
            "fides_key": "data_use_d",
            "active": True,
            "is_default": False,
            "description": "Data Use D",
        }
        data_use_a = DataUse.create(db=db, data=payload_a)
        data_use_b = DataUse.create(db=db, data=payload_b)
        data_use_c = DataUse.create(db=db, data=payload_c)
        data_use_d = DataUse.create(db=db, data=payload_d)

        # Run Update
        auth_header = generate_auth_header([DATA_USE_UPDATE])
        payload = {
            "name": "Data Use C",
            "fides_key": "data_use_c",
            "active": True,
            "description": "Data Use C",
        }
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        # Assert
        a_result = DataUse.get_by(db, field="fides_key", value=data_use_a.fides_key)
        assert a_result.active is True
        b_result = DataUse.get_by(db, field="fides_key", value=data_use_b.fides_key)
        assert b_result.active is True
        c_result = DataUse.get_by(db, field="fides_key", value=data_use_c.fides_key)
        assert c_result.active is True
        d_result = DataUse.get_by(db, field="fides_key", value=data_use_d.fides_key)
        assert d_result.active is False

        # Clean up
        a_result.delete(db)
        b_result.delete(db)
        c_result.delete(db)
        d_result.delete(db)

    def test_update_data_use_deactivate_propagates_down(
            self,
            db: Session,
            api_client: TestClient,
            url,
            generate_auth_header,
    ):
        """
        Tree: A----B----C
                   \
                    ----D
        Current Active Fields: A (true), B (true), C (true), D (true)
        Payload: B: active=False
        Result Active Fields: A (true), B (false), C (false), D (false)
        """
        # Set up Current Taxonomy Tree
        payload_a = {
            "name": "Data Use A",
            "fides_key": "data_use_a",
            "active": True,
            "is_default": False,
            "description": "Data Use A",
        }
        payload_b = {
            "name": "Data Use B",
            "fides_key": "data_use_b",
            "active": True,
            "is_default": False,
            "description": "Data Use B",
        }
        payload_c = {
            "name": "Data Use C",
            "fides_key": "data_use_c",
            "active": True,
            "is_default": False,
            "description": "Data Use C",
        }
        payload_d = {
            "name": "Data Use D",
            "fides_key": "data_use_d",
            "active": True,
            "is_default": False,
            "description": "Data Use D",
        }
        data_use_a = DataUse.create(db=db, data=payload_a)
        data_use_b = DataUse.create(db=db, data=payload_b)
        data_use_c = DataUse.create(db=db, data=payload_c)
        data_use_d = DataUse.create(db=db, data=payload_d)

        # Run Update
        auth_header = generate_auth_header([DATA_USE_UPDATE])
        payload = {
            "name": "Data Use B",
            "fides_key": "data_use_b",
            "active": False,
            "description": "Data Use B",
        }
        response = api_client.put(url, headers=auth_header, json=payload)
        assert 200 == response.status_code

        # Assert
        a_result = DataUse.get_by(db, field="fides_key", value=data_use_a.fides_key)
        assert a_result.active is True
        b_result = DataUse.get_by(db, field="fides_key", value=data_use_b.fides_key)
        assert b_result.active is False
        c_result = DataUse.get_by(db, field="fides_key", value=data_use_c.fides_key)
        assert c_result.active is False
        d_result = DataUse.get_by(db, field="fides_key", value=data_use_d.fides_key)
        assert d_result.active is False

        # Clean up
        a_result.delete(db)
        b_result.delete(db)
        c_result.delete(db)
        d_result.delete(db)