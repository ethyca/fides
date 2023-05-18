# pylint: disable=missing-docstring, redefined-outer-name
"""Integration tests for the API module."""
from json import loads
from typing import Dict, List

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY, model_list, models, parse
from fideslang.models import System as SystemSchema
from pytest import MonkeyPatch
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from starlette.testclient import TestClient

from fides.api.api.v1.scope_registry import (
    CREATE,
    DELETE,
    POLICY_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_READ,
    READ,
    SYSTEM_CREATE,
    SYSTEM_DELETE,
    SYSTEM_UPDATE,
    UPDATE,
)
from fides.api.api.v1.urn_registry import V1_URL_PREFIX
from fides.api.ctl.database.crud import get_resource
from fides.api.ctl.routes import health
from fides.api.ctl.routes.util import API_PREFIX, CLI_SCOPE_PREFIX_MAPPING
from fides.api.ctl.schemas.system import PrivacyDeclarationResponse
from fides.api.ctl.sql_models import Dataset, PrivacyDeclaration, System
from fides.api.oauth.roles import OWNER, VIEWER
from fides.core import api as _api
from fides.core.config import FidesConfig, get_config

CONFIG = get_config()

TAXONOMY_ENDPOINTS = ["data_category", "data_subject", "data_use", "data_qualifier"]


# Helper Functions
def get_existing_key(test_config: FidesConfig, resource_type: str) -> int:
    """Get an ID that is known to exist."""
    return _api.ls(
        test_config.cli.server_url, resource_type, test_config.user.auth_header
    ).json()[-1]["fides_key"]


# Unit Tests
@pytest.mark.unit
def test_generate_resource_urls_no_id(test_config: FidesConfig) -> None:
    """
    Test that the URL generator works as intended.
    """
    server_url = test_config.cli.server_url
    expected_url = f"{server_url}{API_PREFIX}/test/"
    result_url = _api.generate_resource_url(url=server_url, resource_type="test")
    assert expected_url == result_url


@pytest.mark.unit
def test_generate_resource_urls_with_id(test_config: FidesConfig) -> None:
    """
    Test that the URL generator works as intended.
    """
    server_url = test_config.cli.server_url
    expected_url = f"{server_url}{API_PREFIX}/test/1"
    result_url = _api.generate_resource_url(
        url=server_url,
        resource_type="test",
        resource_id="1",
    )
    assert expected_url == result_url


@pytest.mark.integration
class TestCrud:
    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_create(
        self,
        generate_auth_header,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
    ) -> None:
        manifest = resources_dict[endpoint]
        print(manifest.json(exclude_none=True))
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{CREATE}"]
        auth_header = generate_auth_header(scopes=token_scopes)
        result = _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=auth_header,
        )
        print(result.text)
        assert result.status_code == 201

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_create_wrong_scope(
        self,
        generate_auth_header,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
    ) -> None:
        manifest = resources_dict[endpoint]
        token_scopes: List[str] = [PRIVACY_REQUEST_CREATE]
        auth_header = generate_auth_header(scopes=token_scopes)
        result = _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=auth_header,
        )
        assert result.status_code == 403

    async def test_create_dataset_data_categories_validated(
        self, test_config: FidesConfig, resources_dict: Dict
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        manifest.collections[0].data_categories = ["bad_category"]

        result = _api.create(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            json_resource=manifest.json(exclude_none=True),
            resource_type=endpoint,
        )
        assert result.status_code == 422
        assert (
            result.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_ls(
        self, test_config: FidesConfig, endpoint: str, generate_auth_header
    ) -> None:
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{READ}"]
        auth_header = generate_auth_header(scopes=token_scopes)

        result = _api.ls(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            headers=auth_header,
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_ls_wrong_scope(
        self, test_config: FidesConfig, endpoint: str, generate_auth_header
    ) -> None:
        token_scopes: List[str] = [PRIVACY_REQUEST_READ]
        auth_header = generate_auth_header(scopes=token_scopes)

        result = _api.ls(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            headers=auth_header,
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_get(
        self, test_config: FidesConfig, endpoint: str, generate_auth_header
    ) -> None:
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{READ}"]
        auth_header = generate_auth_header(scopes=token_scopes)

        existing_id = get_existing_key(test_config, endpoint)
        result = _api.get(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            resource_id=existing_id,
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_get_wrong_scope(
        self, test_config: FidesConfig, endpoint: str, generate_auth_header
    ) -> None:
        token_scopes: List[str] = [PRIVACY_REQUEST_READ]
        auth_header = generate_auth_header(scopes=token_scopes)

        existing_id = get_existing_key(test_config, endpoint)
        result = _api.get(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            resource_id=existing_id,
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", model_list)
    def test_sent_is_received(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        """
        Confirm that the resource and values that we send are the
        same as the resource that the server returns.
        """
        manifest = resources_dict[endpoint]
        resource_key = manifest.fides_key if endpoint != "user" else manifest.userName

        print(manifest.json(exclude_none=True))
        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resource_id=resource_key,
        )
        print(result.text)
        assert result.status_code == 200
        parsed_result = parse.parse_dict(endpoint, result.json())

        assert parsed_result == manifest

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_update(
        self,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{UPDATE}"]
        auth_header = generate_auth_header(scopes=token_scopes)
        manifest = resources_dict[endpoint]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        print(result.text)
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_update_wrong_scope(
        self,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        token_scopes: List[str] = [POLICY_CREATE_OR_UPDATE]
        auth_header = generate_auth_header(scopes=token_scopes)
        manifest = resources_dict[endpoint]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        assert result.status_code == 403

    async def test_update_dataset_data_categories_validated(
        self, test_config: FidesConfig, resources_dict: Dict
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        manifest.collections[0].data_categories = ["bad_category"]

        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        assert result.status_code == 422
        assert (
            result.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_upsert(
        self,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        token_scopes: List[str] = [
            f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{UPDATE}",
            f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{CREATE}",
        ]
        auth_header = generate_auth_header(scopes=token_scopes)

        manifest = resources_dict[endpoint]
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            resources=[loads(manifest.json())],
        )
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_upsert_wrong_scope(
        self,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        token_scopes: List[str] = [
            f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{CREATE}",
        ]  # Needs both create AND update
        auth_header = generate_auth_header(scopes=token_scopes)

        manifest = resources_dict[endpoint]
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            resources=[loads(manifest.json())],
        )
        assert result.status_code == 403

    async def test_upsert_validates_resources_against_pydantic_model(
        self, test_config: FidesConfig, resources_dict: Dict, async_session
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        dict_manifest = manifest.dict()
        del dict_manifest["organization_fides_key"]

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resources=[dict_manifest],
        )
        assert result.status_code == 200

        resource = await get_resource(Dataset, manifest.fides_key, async_session)
        assert resource.organization_fides_key == "default_organization"

    async def test_upsert_dataset_data_categories_validated(
        self, test_config: FidesConfig, resources_dict: Dict
    ):
        endpoint = "dataset"
        manifest: Dataset = resources_dict[endpoint]
        dict_manifest = manifest.dict()
        dict_manifest["collections"][0]["data_categories"] = ["bad_category"]

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resources=[dict_manifest],
        )
        assert result.status_code == 422
        assert (
            result.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_delete_wrong_scope(
        self,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        token_scopes: List[str] = [PRIVACY_REQUEST_DELETE]
        auth_header = generate_auth_header(scopes=token_scopes)

        manifest = resources_dict[endpoint]
        resource_key = manifest.fides_key if endpoint != "user" else manifest.userName

        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=resource_key,
            headers=auth_header,
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", model_list)
    def test_api_delete(
        self,
        test_config: FidesConfig,
        resources_dict: Dict,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{DELETE}"]
        auth_header = generate_auth_header(scopes=token_scopes)

        manifest = resources_dict[endpoint]
        resource_key = manifest.fides_key if endpoint != "user" else manifest.userName

        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=resource_key,
            headers=auth_header,
        )
        print(result.text)
        assert result.status_code == 200
        resp = result.json()
        assert resp["message"] == "resource deleted"
        assert resp["resource"]["fides_key"] == manifest.fides_key


@pytest.mark.unit
class TestSystemCreate:
    @pytest.fixture(scope="function", autouse=True)
    def remove_all_systems(self, db) -> SystemSchema:
        """Remove any systems (and privacy declarations) before test execution for clean state"""
        for privacy_declaration in PrivacyDeclaration.all(db):
            privacy_declaration.delete(db)
        for system in System.all(db):
            system.delete(db)

    @pytest.fixture(scope="function")
    def system_create_request_body(self) -> SystemSchema:
        return SystemSchema(
            organization_fides_key=1,
            registryId=1,
            fides_key="system_fides_key",
            system_type="SYSTEM",
            name="Test System",
            description="A Test System",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="provide",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=[],
                ),
                models.PrivacyDeclaration(
                    name="declaration-name-2",
                    data_categories=[],
                    data_use="advertising",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=[],
                ),
            ],
            system_dependencies=[],
        )

    def test_system_create_not_authenticated(
        self,
        test_config,
        system_create_request_body,
        db,
    ):
        result = _api.create(
            url=test_config.cli.server_url,
            headers={},
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_401_UNAUTHORIZED
        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_no_direct_scope(
        self,
        test_config,
        generate_auth_header,
        system_create_request_body,
        db,
    ):
        auth_header = generate_auth_header(scopes=[POLICY_CREATE_OR_UPDATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_403_FORBIDDEN

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_no_encompassing_role(
        self,
        test_config,
        system_create_request_body,
        db,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_403_FORBIDDEN

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_system_already_exists(
        self,
        test_config,
        system,
        system_create_request_body,
        db,
        generate_auth_header,
    ):
        system_create_request_body.fides_key = system.fides_key
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])
        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_409_CONFLICT

        assert (
            len(System.all(db)) == 1
        )  # ensure our system wasn't created, still only one system

    async def test_system_create(
        self, generate_auth_header, db, test_config, system_create_request_body
    ):
        """Ensure system create works for base case, which includes 2 privacy declarations"""
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_201_CREATED
        assert result.json()["name"] == "Test System"
        assert len(result.json()["privacy_declarations"]) == 2

        systems = System.all(db)
        assert len(systems) == 1
        assert systems[0].name == "Test System"
        assert len(systems[0].privacy_declarations) == 2

    def test_system_create_has_role_that_can_update_all_systems(
        self,
        test_config,
        system_create_request_body,
        db,
        generate_role_header,
    ):
        """Ensure system create works for owner role, which has necessary scope"""
        auth_header = generate_role_header(roles=[OWNER])
        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_201_CREATED
        assert result.json()["name"] == "Test System"
        assert len(result.json()["privacy_declarations"]) == 2

        systems = System.all(db)
        assert len(systems) == 1
        assert systems[0].name == "Test System"
        assert len(systems[0].privacy_declarations) == 2

    async def test_system_create_no_privacy_declarations(
        self, generate_auth_header, db, test_config, system_create_request_body
    ):
        """Ensure system create works even with no privacy declarations passed"""
        system_create_request_body.privacy_declarations = []
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_201_CREATED
        assert result.json()["name"] == "Test System"
        assert len(result.json()["privacy_declarations"]) == 0

        systems = System.all(db)
        assert len(systems) == 1
        assert systems[0].name == "Test System"
        assert len(systems[0].privacy_declarations) == 0

    async def test_system_create_invalid_privacy_declarations(
        self, generate_auth_header, db, test_config, system_create_request_body
    ):
        """Ensure system create errors with invalid privacy declarations"""
        system_create_request_body.privacy_declarations[1].data_use = None
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert len(System.all(db)) == 0  # ensure our system wasn't created
        assert (
            len(PrivacyDeclaration.all(db)) == 0
        )  # ensure neither of our declarations were created

        system_create_request_body.privacy_declarations[1].data_use = "invalid_data_use"
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert len(System.all(db)) == 0  # ensure our system wasn't created
        assert (
            len(PrivacyDeclaration.all(db)) == 0
        )  # ensure neither of our declarations were created


@pytest.mark.unit
class TestSystemUpdate:
    updated_system_name = "Updated System Name"

    @pytest.fixture(scope="function", autouse=True)
    def remove_all_systems(self, db) -> SystemSchema:
        """Remove any systems (and privacy declarations) before test execution for clean state"""
        for privacy_declaration in PrivacyDeclaration.all(db):
            privacy_declaration.delete(db)
        for system in System.all(db):
            system.delete(db)

    @pytest.fixture(scope="function")
    def system_update_request_body(self, system) -> SystemSchema:
        return SystemSchema(
            organization_fides_key=1,
            registryId=1,
            fides_key=system.fides_key,
            system_type="SYSTEM",
            name=self.updated_system_name,
            description="Test Policy",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="provide",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=[],
                )
            ],
            system_dependencies=[],
        )

    def test_system_update_not_authenticated(
        self, test_config, system_update_request_body
    ):
        result = _api.update(
            url=test_config.cli.server_url,
            headers={},
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_401_UNAUTHORIZED

    def test_system_update_no_direct_scope(
        self,
        test_config,
        generate_auth_header,
        system_update_request_body,
        db,
        system,
    ):
        auth_header = generate_auth_header(scopes=[POLICY_CREATE_OR_UPDATE])

        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_403_FORBIDDEN

        db.refresh(system)
        assert system.name != self.updated_system_name

    async def test_system_update_has_direct_scope(
        self, generate_auth_header, system, db, test_config, system_update_request_body
    ):
        assert system.name != self.updated_system_name
        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])

        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_200_OK
        assert result.json()["name"] == self.updated_system_name
        assert len(result.json()["privacy_declarations"]) == 1
        assert (
            result.json()["privacy_declarations"][0]["data_use"]
            == system_update_request_body.privacy_declarations[0].data_use
        )

        db.refresh(system)
        assert system.name == self.updated_system_name
        assert len(system.privacy_declarations) == 1
        assert (
            system.privacy_declarations[0].data_use
            == system_update_request_body.privacy_declarations[0].data_use
        )

    def test_system_update_no_encompassing_role(
        self,
        test_config,
        system_update_request_body,
        system,
        db,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_403_FORBIDDEN

        db.refresh(system)
        assert system.name != self.updated_system_name

    def test_system_update_has_role_that_can_update_all_systems(
        self,
        test_config,
        system_update_request_body,
        system,
        db,
        generate_role_header,
    ):
        assert system.name != self.updated_system_name
        auth_header = generate_role_header(roles=[OWNER])
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_200_OK
        assert result.json()["name"] == self.updated_system_name

        db.refresh(system)
        assert system.name == self.updated_system_name

    def test_system_update_as_system_manager(
        self,
        test_config,
        system_update_request_body,
        system,
        db,
        generate_system_manager_header,
    ):
        assert system.name != self.updated_system_name

        auth_header = generate_system_manager_header([system.id])
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_200_OK
        assert result.json()["name"] == self.updated_system_name

        db.refresh(system)
        assert system.name == self.updated_system_name

    def test_system_update_as_system_manager_403_if_not_found(
        self,
        test_config,
        system_update_request_body,
        system,
        generate_system_manager_header,
    ):
        auth_header = generate_system_manager_header([system.id])
        system_update_request_body.fides_key = "system-does-not-exist"
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_403_FORBIDDEN

    def test_system_update_as_owner_404_if_not_found(
        self,
        test_config,
        system_update_request_body,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.fides_key = "system-does-not-exist"
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_404_NOT_FOUND

    def test_system_update_privacy_declaration_invalid_data_use(
        self,
        system,
        test_config,
        system_update_request_body,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.privacy_declarations[0].data_use = "invalid_data_use"
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_use == "advertising"

    def test_system_update_privacy_declaration_invalid_duplicate(
        self,
        system,
        test_config,
        system_update_request_body,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])

        # test that 'exact' duplicate fails (data_use and name match)
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="declaration-name",  # same as initial PrivacyDeclaration
                data_categories=["user.payment"],  # other fields can differ
                data_use="provide",  # same as initial PrivacyDeclaration
                data_subjects=["anonymous_user"],  # other fields can differ
                data_qualifier="aggregated",  # other fields can differ
                dataset_references=[],
            )
        )
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_use == "advertising"

        # test that duplicate with no name on either declaration fails
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="",  # no name specified
                data_categories=["user.payment"],
                data_use="provide",  # identical data use
                data_subjects=["anonymous_user"],  # other fields can differ
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="",  # no name specified
                data_categories=["user.payment"],
                data_use="provide",  # identicial data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_use == "advertising"

        # test that duplicate data_use with no name on one declaration succeeds
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="",  # no name specified
                data_categories=["user.payment"],
                data_use="provide",  # identical data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration",  # this name distinguishes the declaration from the above
                data_categories=["user.payment"],
                data_use="provide",  # identicial data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_200_OK
        # assert the system's privacy declarations have been updated
        db.refresh(system)
        # both declarations should have 'provide' data_use since the update was allowed
        assert system.privacy_declarations[0].data_use == "provide"
        assert system.privacy_declarations[1].data_use == "provide"

        # test that duplicate data_use with differeing names on declarations succeeds
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 1",  # specify a unique name here
                data_categories=["user.payment"],
                data_use="advertising",  # identical data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 2",  # this name distinguishes the declaration from the above
                data_categories=["user.payment"],
                data_use="advertising",  # identicial data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_200_OK
        # assert the system's privacy declarations have been updated
        db.refresh(system)
        # both declarations should have 'advertising' data_use since the update was allowed
        assert system.privacy_declarations[0].data_use == "advertising"
        assert system.privacy_declarations[1].data_use == "advertising"

        # test that differeing data_use with same names on declarations succeeds
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 1",  # identical name
                data_categories=["user.payment"],
                data_use="advertising",  # differing data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 1",  # identical name
                data_categories=["user.payment"],
                data_use="provide",  # differing data use
                data_subjects=["anonymous_user"],
                data_qualifier="aggregated",
                dataset_references=[],
            )
        )
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_200_OK
        # assert the system's privacy declarations have been updated
        db.refresh(system)
        # should be one declaration with advertising, one with provide
        assert (
            system.privacy_declarations[0].data_use == "advertising"
            and system.privacy_declarations[1].data_use == "provide"
        ) or (
            system.privacy_declarations[1].data_use == "advertising"
            and system.privacy_declarations[0].data_use == "provide"
        )
        assert (
            system.privacy_declarations[0].name == "new declaration 1"
            and system.privacy_declarations[1].name == "new declaration 1"
        )

    @pytest.mark.parametrize(
        "update_declarations",
        [
            (
                [  # add a privacy declaration distinct from existing declaration
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="provide",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    )
                ]
            ),
            (
                # add 2 privacy declarations distinct from existing declaration
                [
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="provide",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # add 2 privacy declarations, one the same data use and name as existing
                [
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # add 2 privacy declarations, one the same data use and name as existing, other same data use
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # specify no declarations, declarations should be cleared off the system
                []
            ),
        ],
    )
    def test_system_update_updates_declarations(
        self,
        db,
        test_config,
        system,
        generate_auth_header,
        system_update_request_body,
        update_declarations,
    ):
        """
        Test to assert that our `PUT` endpoint acts in a fully declarative manner, putting the DB state of the
        system's privacy requests in *exactly* the same state as specified on the request payload.

        This is executed against various different sets of input privacy declarations to ensure it works
        in a variety of scenarios
        """

        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])
        system_update_request_body.privacy_declarations = update_declarations
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )

        # assert the declarations in our responses match those in our requests
        response_decs: List[dict] = result.json()["privacy_declarations"]
        # remove the IDs from the response decs for easier matching with request payload
        # we also are implicitly affirming the response declarations DO have an
        # 'id' field, as we expect
        for response_dec in response_decs:
            response_dec.pop("id")
        for update_dec in update_declarations:
            response_decs.remove(update_dec.dict())
        # and assert we don't have any extra response declarations
        assert len(response_decs) == 0

        # do the same for the declarations in our db record
        system = System.all(db)[0]
        db.refresh(system)
        db_decs = [
            models.PrivacyDeclaration.from_orm(db_dec)
            for db_dec in system.privacy_declarations
        ]

        for update_dec in update_declarations:
            db_decs.remove(update_dec.dict())
        # and assert we don't have any extra response declarations
        assert len(db_decs) == 0

    @pytest.mark.parametrize(
        "update_declarations",
        [
            (
                [  # update a dec matching one existing dec
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    )
                ]
            ),
            (
                [  # add a new single dec with same data use
                    models.PrivacyDeclaration(
                        name="declaration-name-1",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    )
                ]
            ),
            (
                [  # add a new single dec with same data use, no name
                    models.PrivacyDeclaration(
                        name="",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    )
                ]
            ),
            (
                # update 2 privacy declarations both matching existing decs
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="Collect data for third party sharing",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # update 2 privacy declarations, one with matching name and data use, other only data use
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # update 2 privacy declarations, one with matching name and data use, other only data use but same data use
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # update 2 privacy declarations, one with only matching data use, other totally new
                [
                    models.PrivacyDeclaration(
                        name="declaration-name-1",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="provide",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # add 2 new privacy declarations
                [
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="provide",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="improve",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # add 2 new privacy declarations, same data uses as existing decs but no names
                [
                    models.PrivacyDeclaration(
                        name="",
                        data_categories=[],
                        data_use="advertising",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        data_qualifier="aggregated_data",
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # specify no declarations, declarations should be cleared off the system
                []
            ),
        ],
    )
    def test_system_update_manages_declaration_records(
        self,
        db,
        test_config,
        system_multiple_decs: System,
        generate_auth_header,
        system_update_request_body,
        update_declarations,
    ):
        """
        Test to assert that existing privacy declaration records stay constant when necessary
        """
        old_db_decs = [
            PrivacyDeclarationResponse.from_orm(dec)
            for dec in system_multiple_decs.privacy_declarations
        ]
        old_decs_updated = [
            old_db_dec
            for old_db_dec in old_db_decs
            if any(
                (
                    old_db_dec.name == update_declaration.name
                    and old_db_dec.data_use == update_declaration.data_use
                )
                for update_declaration in update_declarations
            )
        ]
        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])
        system_update_request_body.privacy_declarations = update_declarations
        _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )

        db.refresh(system_multiple_decs)
        updated_decs: List[
            PrivacyDeclaration
        ] = system_multiple_decs.privacy_declarations.copy()

        for old_dec_updated in old_decs_updated:
            updated_dec = next(
                updated_dec
                for updated_dec in updated_decs
                if updated_dec.name == old_dec_updated.name
                and updated_dec.data_use == old_dec_updated.data_use
            )
            # assert that the updated dec in the DB kept the same ID
            assert updated_dec.id == old_dec_updated.id

            # remove from our lists to check since we've confirmed ID stayed constant
            updated_decs.remove(updated_dec)
            old_db_decs.remove(old_dec_updated)

        # our old db decs that were _not_ updated should no longer be in the db
        for old_db_dec in old_db_decs:
            assert not any(
                old_db_dec.id == updated_dec.id for updated_dec in updated_decs
            )

        # and just verify that we have same number of privacy declarations in db as specified in the update request
        assert len(PrivacyDeclaration.all(db)) == len(update_declarations)


@pytest.mark.unit
class TestSystemDelete:
    @pytest.fixture(scope="function")
    def url(self, system) -> str:
        return V1_URL_PREFIX + f"/system/{system.fides_key}"

    def test_system_delete_not_authenticated(self, test_config, system):
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers={},
        )
        assert result.status_code == HTTP_401_UNAUTHORIZED

    def test_system_delete_no_direct_scope(
        self,
        test_config,
        url,
        system,
        generate_auth_header,
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=auth_header,
        )

        assert result.status_code == HTTP_403_FORBIDDEN

    def test_system_delete_has_direct_scope(
        self, test_config, generate_auth_header, system
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_DELETE])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=auth_header,
        )

        assert result.status_code == HTTP_200_OK
        assert result.json()["message"] == "resource deleted"
        assert result.json()["resource"]["fides_key"] == system.fides_key

    def test_system_delete_no_encompassing_role(
        self, test_config, generate_role_header, system
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=auth_header,
        )
        assert result.status_code == HTTP_403_FORBIDDEN

    def test_system_delete_has_role_that_can_delete_systems(
        self,
        test_config,
        system,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=auth_header,
        )
        assert result.status_code == HTTP_200_OK
        assert result.json()["message"] == "resource deleted"
        assert result.json()["resource"]["fides_key"] == system.fides_key

    def test_system_delete_as_system_manager(
        self,
        test_config,
        system,
        generate_system_manager_header,
    ):
        auth_header = generate_system_manager_header([system.id])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=auth_header,
        )
        assert result.status_code == HTTP_200_OK
        assert result.json()["message"] == "resource deleted"
        assert result.json()["resource"]["fides_key"] == system.fides_key

    def test_owner_role_gets_404_if_system_not_found(
        self,
        test_config,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id="bad_fides_key",
            headers=auth_header,
        )
        assert result.status_code == HTTP_404_NOT_FOUND

    def test_system_manager_gets_403_if_system_not_found(
        self, test_config, system, generate_system_manager_header
    ):
        auth_header = generate_system_manager_header([system.id])
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id="bad_fides_key",
            headers=auth_header,
        )
        assert result.status_code == HTTP_403_FORBIDDEN


@pytest.mark.integration
class TestDefaultTaxonomyCrud:
    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_delete_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        resource = getattr(DEFAULT_TAXONOMY, endpoint)[0]

        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=resource.fides_key,
            headers=test_config.user.auth_header,
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_can_update_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        """Should be able to update as long as `is_default` is not changing"""
        resource = getattr(DEFAULT_TAXONOMY, endpoint)[0]
        json_resource = resource.json(exclude_none=True)

        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            json_resource=json_resource,
        )
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_can_upsert_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        """Should be able to upsert as long as `is_default` is not changing"""
        resources = [r.dict() for r in getattr(DEFAULT_TAXONOMY, endpoint)[0:2]]
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resources=resources,
        )
        assert result.status_code == 200

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_create_default_taxonomy(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        manifest.is_default = True
        result = _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=test_config.user.auth_header,
        )
        assert result.status_code == 403

        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=manifest.fides_key,
            headers=test_config.user.auth_header,
        )

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_upsert_default_taxonomy(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        manifest.is_default = True
        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resources=[manifest.dict()],
        )
        assert result.status_code == 403

        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=manifest.fides_key,
            headers=test_config.user.auth_header,
        )

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_update_is_default(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=test_config.user.auth_header,
        )

        manifest.is_default = True
        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        assert result.status_code == 403

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_upsert_is_default(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        manifest.is_default = True
        second_item = manifest.copy()
        second_item.is_default = False

        _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=second_item.json(exclude_none=True),
            headers=test_config.user.auth_header,
        )

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resources=[manifest.dict(), second_item.dict()],
        )
        assert result.status_code == 403

        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=manifest.fides_key,
            headers=test_config.user.auth_header,
        )
        _api.delete(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            resource_id=second_item.fides_key,
            headers=test_config.user.auth_header,
        )


@pytest.mark.integration
def test_static_sink(test_config: FidesConfig) -> None:
    """Make sure we are hosting something at / and not getting a 404"""
    response = requests.get(f"{test_config.cli.server_url}")
    assert response.status_code == 200


@pytest.mark.integration
def test_404_on_api_routes(test_config: FidesConfig) -> None:
    """Should get a 404 on routes that start with API_PREFIX but do not exist"""
    response = requests.get(
        f"{test_config.cli.server_url}{API_PREFIX}/path/that/does/not/exist"
    )
    assert response.status_code == 404


# Integration Tests
@pytest.mark.integration
@pytest.mark.parametrize(
    "database_health, expected_status_code",
    [("healthy", 200), ("needs migration", 200), ("unhealthy", 503)],
)
def test_api_ping(
    test_config: FidesConfig,
    database_health: str,
    expected_status_code: int,
    monkeypatch: MonkeyPatch,
    test_client: TestClient,
) -> None:
    def mock_get_db_health(url: str, db) -> str:
        return database_health

    monkeypatch.setattr(health, "get_db_health", mock_get_db_health)
    response = test_client.get(test_config.cli.server_url + "/health")
    assert response.status_code == expected_status_code


@pytest.mark.integration
@pytest.mark.parametrize("endpoint_name", [f"{API_PREFIX}/organization", "/health"])
def test_trailing_slash(test_config: FidesConfig, endpoint_name: str) -> None:
    """URLs both with and without a trailing slash should resolve and not 404"""
    url = f"{test_config.cli.server_url}{endpoint_name}"
    response = requests.get(url, headers=CONFIG.user.auth_header)
    assert response.status_code == 200
    response = requests.get(f"{url}/", headers=CONFIG.user.auth_header)
    assert response.status_code == 200
