# pylint: disable=missing-docstring, redefined-outer-name
"""Integration tests for the API module."""
import json
import typing
from datetime import datetime, timezone
from json import loads
from typing import Dict, List, Tuple
from uuid import uuid4

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY, model_list, models, parse
from fideslang.models import PrivacyDeclaration as PrivacyDeclarationSchema
from fideslang.models import System as SystemSchema
from pytest import MonkeyPatch
from sqlalchemy import text
from sqlalchemy.orm import Session
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

from fides.api.api.v1.endpoints import health
from fides.api.db.crud import get_resource
from fides.api.db.system import create_system
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import DataCategory as DataCategoryModel
from fides.api.models.sql_models import Dataset
from fides.api.models.sql_models import DataSubject as DataSubjectModel
from fides.api.models.sql_models import DataUse as DataUseModel
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.models.system_history import SystemHistory
from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.oauth.roles import OWNER, VIEWER
from fides.api.schemas.system import PrivacyDeclarationResponse, SystemResponse
from fides.api.schemas.taxonomy_extensions import DataCategory, DataSubject, DataUse
from fides.api.util.endpoint_utils import API_PREFIX, CLI_SCOPE_PREFIX_MAPPING
from fides.common.api.scope_registry import (
    CREATE,
    DELETE,
    POLICY_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_READ,
    READ,
    SYSTEM_CREATE,
    SYSTEM_DELETE,
    SYSTEM_READ,
    SYSTEM_UPDATE,
    UPDATE,
)
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from fides.config import FidesConfig, get_config
from fides.core import api as _api

CONFIG = get_config()

TAXONOMY_ENDPOINTS = ["data_category", "data_subject", "data_use"]
TAXONOMY_EXTENSIONS = {
    "data_category": DataCategory,
    "data_subject": DataSubject,
    "data_use": DataUse,
}


# Helper Functions
def get_existing_key(test_config: FidesConfig, resource_type: str) -> int:
    """Get an ID that is known to exist."""
    return _api.ls(
        test_config.cli.server_url, resource_type, test_config.user.auth_header
    ).json()[-1]["fides_key"]


@pytest.fixture(scope="function", name="inactive_data_category")
def fixture_inactive_data_category(db: Session) -> typing.Generator:
    """
    Fixture that yields an inactive data category and then deletes it for each test run.
    """
    fides_key = "inactive_data_category"
    data_category = DataCategoryModel.create(
        db=db,
        data={
            "fides_key": fides_key,
            "name": "Inactive Category",
            "active": False,
        },
    )

    yield data_category

    data_category.delete(db)


@pytest.fixture(scope="function", name="inactive_data_use")
def fixture_inactive_data_use(db: Session) -> typing.Generator:
    """
    Fixture that yields an inactive data use and then deletes it for each test run.
    """
    fides_key = "inactive_data_use"
    data_use = DataUseModel.create(
        db=db,
        data={
            "fides_key": fides_key,
            "name": "Inactive Use",
            "active": False,
        },
    )

    yield data_use

    data_use.delete(db)


@pytest.fixture(scope="function", name="inactive_data_subject")
def fixture_inactive_data_subject(db: Session) -> typing.Generator:
    """
    Fixture that yields an inactive data subject and then deletes it for each test run.
    """
    fides_key = "inactive_data_subject"
    data_subject = DataSubjectModel.create(
        db=db,
        data={
            "fides_key": fides_key,
            "name": "Inactive Subject",
            "active": False,
        },
    )

    yield data_subject

    data_subject.delete(db)


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
            == "Value error, The data category bad_category is not supported."
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
            == "Value error, The data category bad_category is not supported."
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
        dict_manifest = manifest.model_dump(mode="json")
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
        dict_manifest = manifest.model_dump(mode="json")
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
            == "Value error, The data category bad_category is not supported."
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
    def remove_all_systems(self, db) -> None:
        """Remove any systems (and privacy declarations) before test execution for clean state"""
        for privacy_declaration in PrivacyDeclaration.all(db):
            privacy_declaration.delete(db)
        for system in System.all(db):
            system.delete(db)

    @pytest.fixture(scope="function")
    def system_create_request_body(self) -> SystemSchema:
        return SystemSchema(
            organization_fides_key="1",
            fides_key="system_fides_key",
            system_type="SYSTEM",
            name="Test System",
            description="A Test System",
            vendor_id="test_vendor",
            dataset_references=["another_system_reference"],
            processes_personal_data=True,
            exempt_from_privacy_regulations=False,
            reason_for_exemption=None,
            uses_profiling=True,
            legal_basis_for_profiling=["Authorised by law", "Contract"],
            does_international_transfers=True,
            legal_basis_for_transfers=["Adequacy Decision", "BCRs"],
            requires_data_protection_assessments=True,
            dpa_location="https://www.example.com/dpa",
            dpa_progress="pending",
            privacy_policy="https://www.example.com/privacy_policy",
            legal_name="Sunshine Corporation",
            legal_address="35925 Test Lane, Test Town, TX 24924",
            responsibility=["Processor"],
            dpo="John Doe, CIPT",
            joint_controller_info="Jane Doe",
            data_security_practices="We encrypt all your data in transit and at rest",
            cookie_max_age_seconds="31536000",
            uses_cookies=True,
            cookie_refresh=True,
            uses_non_cookie_access=True,
            legitimate_interest_disclosure_url="http://www.example.com/legitimate_interest_disclosure",
            meta={},
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=["another_system_reference"],
                    features=["Link different devices"],
                    legal_basis_for_processing="Public interest",
                    impact_assessment_location="https://www.example.com/impact_assessment_location",
                    retention_period="3-5 years",
                    processes_special_category_data=True,
                    special_category_legal_basis="Reasons of substantial public interest (with a basis in law)",
                    data_shared_with_third_parties=True,
                    third_parties="Third Party Marketing Dept.",
                    shared_categories=["user"],
                    cookies=[
                        {
                            "name": "essential_cookie",
                            "path": "/",
                            "domain": "example.com",
                        }
                    ],
                ),
                models.PrivacyDeclaration(
                    name="declaration-name-2",
                    data_categories=[],
                    data_use="marketing.advertising",
                    data_subjects=[],
                    dataset_references=[],
                ),
            ],
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

    def test_system_create_invalid_data_category(
        self, test_config, db, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": [
                                "user.name.first",
                                "user.name.nickname",
                                "user.name.last",
                            ],  # Nickname does not exist
                            "data_use": "marketing",
                        }
                    ],
                }
            ),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": "Invalid privacy declaration referencing unknown DataCategory user.name.nickname"
        }

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_invalid_data_subject(
        self, test_config, db, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": ["user.name.first", "user.name.last"],
                            "data_use": "marketing",
                            "data_subjects": [
                                "employee",
                                "intern",
                            ],  # Intern does not exist
                        }
                    ],
                }
            ),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": "Invalid privacy declaration referencing unknown DataSubject intern"
        }

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_invalid_data_use(
        self, test_config, db, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": ["user.name.first", "user.name.last"],
                            "data_use": "marketing.measure",  # Invalid data use
                        }
                    ],
                }
            ),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": "Invalid privacy declaration referencing unknown DataUse marketing.measure"
        }

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_inactive_data_category(
        self, test_config, inactive_data_category, db, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": [
                                "user.name.first",
                                "user.name.last",
                                inactive_data_category.fides_key,
                            ],
                            "data_use": "marketing",
                        }
                    ],
                }
            ),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": f"Invalid privacy declaration referencing inactive DataCategory {inactive_data_category.fides_key}"
        }

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_inactive_data_use(
        self, test_config, inactive_data_use, db, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": [
                                "user.name.first",
                                "user.name.last",
                            ],
                            "data_use": inactive_data_use.fides_key,
                        }
                    ],
                }
            ),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": f"Invalid privacy declaration referencing inactive DataUse {inactive_data_use.fides_key}"
        }

        assert not System.all(db)  # ensure our system wasn't created

    def test_system_create_inactive_data_subject(
        self, test_config, inactive_data_subject, db, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": [
                                "user.name.first",
                                "user.name.last",
                            ],
                            "data_use": "marketing",
                            "data_subjects": [inactive_data_subject.fides_key],
                        }
                    ],
                }
            ),
        )

        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": f"Invalid privacy declaration referencing inactive DataSubject {inactive_data_subject.fides_key}"
        }

        assert not System.all(db)  # ensure our system wasn't created

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
        json_results = result.json()
        assert json_results["cookies"] == []  # No cookies at System level
        assert json_results["privacy_declarations"][0]["cookies"] == [
            {"name": "essential_cookie", "path": "/", "domain": "example.com"}
        ]
        assert json_results["privacy_declarations"][1]["cookies"] == []
        assert json_results["data_stewards"] == []

        systems = System.all(db)
        assert len(systems) == 1
        system = systems[0]

        for field in SystemResponse.model_fields:
            system_val = getattr(system, field)
            if isinstance(system_val, typing.Hashable) and not isinstance(
                system_val, datetime
            ):
                assert system_val == json_results[field]
        assert len(json_results["privacy_declarations"]) == 2
        assert json_results["created_at"]

        for i, decl in enumerate(system.privacy_declarations):
            for field in PrivacyDeclarationResponse.model_fields:
                decl_val = getattr(decl, field)
                if isinstance(decl_val, typing.Hashable):
                    assert decl_val == json_results["privacy_declarations"][i][field]

        assert len(system.privacy_declarations) == 2

        assert system.name == "Test System"
        assert system.vendor_id == "test_vendor"
        assert system.dataset_references == ["another_system_reference"]
        assert system.processes_personal_data is True
        assert system.exempt_from_privacy_regulations is False
        assert system.reason_for_exemption is None
        assert system.uses_profiling is True
        assert system.legal_basis_for_profiling == ["Authorised by law", "Contract"]
        assert system.does_international_transfers is True
        assert system.legal_basis_for_transfers == ["Adequacy Decision", "BCRs"]
        assert system.requires_data_protection_assessments is True
        assert system.dpa_location == "https://www.example.com/dpa"
        assert system.dpa_progress == "pending"
        assert system.privacy_policy == "https://www.example.com/privacy_policy"
        assert system.legal_name == "Sunshine Corporation"
        assert system.legal_address == "35925 Test Lane, Test Town, TX 24924"
        assert system.responsibility == ["Processor"]
        assert system.dpo == "John Doe, CIPT"
        assert system.joint_controller_info == "Jane Doe"
        assert (
            system.data_security_practices
            == "We encrypt all your data in transit and at rest"
        )
        assert system.cookie_max_age_seconds == 31536000
        assert system.uses_cookies is True
        assert system.cookie_refresh is True
        assert system.uses_non_cookie_access is True
        assert (
            system.legitimate_interest_disclosure_url
            == "http://www.example.com/legitimate_interest_disclosure"
        )
        assert system.data_stewards == []
        assert [cookie.name for cookie in systems[0].cookies] == []
        assert [
            cookie.name for cookie in systems[0].privacy_declarations[0].cookies
        ] == ["essential_cookie"]
        assert systems[0].privacy_declarations[1].cookies == []

        privacy_decl = system.privacy_declarations[0]
        assert privacy_decl.name == "declaration-name"
        assert privacy_decl.dataset_references == ["another_system_reference"]
        assert privacy_decl.features == ["Link different devices"]
        assert privacy_decl.legal_basis_for_processing == "Public interest"
        assert (
            await privacy_decl.get_purpose_legal_basis_override() == "Public interest"
        )
        assert (
            privacy_decl.impact_assessment_location
            == "https://www.example.com/impact_assessment_location"
        )
        assert privacy_decl.retention_period == "3-5 years"
        assert privacy_decl.processes_special_category_data is True
        assert (
            privacy_decl.special_category_legal_basis
            == "Reasons of substantial public interest (with a basis in law)"
        )
        assert privacy_decl.data_shared_with_third_parties is True
        assert privacy_decl.third_parties == "Third Party Marketing Dept."
        assert privacy_decl.shared_categories == ["user"]
        assert privacy_decl.flexible_legal_basis_for_processing is True

    async def test_system_create_minimal_request_body(
        self, generate_auth_header, db, test_config, system_create_request_body
    ):
        """Assert system default fields are what is expected when a very minimal system request is sent"""
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=json.dumps(
                {
                    "fides_key": "system_key",
                    "system_type": "system",
                    "privacy_declarations": [
                        {
                            "fides_key": "test",
                            "data_categories": ["user"],
                            "data_use": "marketing",
                        }
                    ],
                }
            ),
        )
        assert result.status_code == HTTP_201_CREATED
        systems = System.all(db)
        assert len(systems) == 1
        system = systems[0]

        expected_none = [
            "connection_configs",
            "data_security_practices",
            "description",
            "dpa_location",
            "dpa_progress",
            "dpo",
            "egress",
            "fidesctl_meta",
            "ingress",
            "joint_controller_info",
            "legal_address",
            "legal_name",
            "meta",
            "name",
            "privacy_policy",
            "reason_for_exemption",
            "tags",
            "vendor_id",
        ]
        for field in expected_none:
            assert getattr(system, field) is None

        assert system.processes_personal_data is True

        expected_false = [
            "does_international_transfers",
            "exempt_from_privacy_regulations",
            "requires_data_protection_assessments",
            "uses_profiling",
        ]

        for field in expected_false:
            assert getattr(system, field) is False

        expected_empty_list = [
            "cookies",
            "dataset_references",
            "data_stewards",
            "legal_basis_for_profiling",
            "legal_basis_for_transfers",
            "responsibility",
        ]
        for field in expected_empty_list:
            assert getattr(system, field) == []

        privacy_declaration = system.privacy_declarations[0]

        expected_none_privacy_declaration_fields = [
            "dataset_references",
            "egress",
            "impact_assessment_location",
            "ingress",
            "legal_basis_for_processing",
            "name",
            "retention_period",
            "special_category_legal_basis",
            "third_parties",
        ]
        for field in expected_none_privacy_declaration_fields:
            assert getattr(privacy_declaration, field) is None

        expected_false_pd_fields = [
            "data_shared_with_third_parties",
            "processes_special_category_data",
        ]
        for field in expected_false_pd_fields:
            assert getattr(privacy_declaration, field) is False

        expected_empty_list_pd_fields = [
            "cookies",
            "data_subjects",
            "features",
            "shared_categories",
        ]
        for field in expected_empty_list_pd_fields:
            assert getattr(privacy_declaration, field) == []

        assert privacy_declaration.system_id == system.id
        assert privacy_declaration.data_use == "marketing"
        assert privacy_declaration.data_categories == ["user"]

    async def test_system_create_custom_metadata_saas_config(
        self,
        generate_auth_header,
        db,
        test_config,
        system_create_request_body: SystemSchema,
    ):
        """Ensure system create works with custom metadata, including tested objects"""
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])
        system_create_request_body.meta = {
            "saas_config": {
                "type": "stripe",
                "icon": "test",
            }
        }
        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_201_CREATED
        assert result.json()["name"] == "Test System"
        assert len(result.json()["privacy_declarations"]) == 2

        assert result.json()["meta"] == {
            "saas_config": {
                "type": "stripe",
                "icon": "test",
            }
        }

        systems = System.all(db)
        assert len(systems) == 1
        assert systems[0].name == "Test System"
        assert len(systems[0].privacy_declarations) == 2
        assert systems[0].meta == {
            "saas_config": {
                "type": "stripe",
                "icon": "test",
            }
        }

        # and assert we can retrieve the custom metadata property via API (`GET`)
        auth_header = generate_auth_header(scopes=[SYSTEM_READ])
        get_response = _api.get(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            resource_id=systems[0].fides_key,
        )
        assert get_response.json()["meta"] == {
            "saas_config": {
                "type": "stripe",
                "icon": "test",
            }
        }

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

    async def test_system_create_invalid_legal_basis_for_profiling(
        self, generate_auth_header, test_config, system_create_request_body
    ):
        system_create_request_body.legal_basis_for_profiling = ["bad_basis"]
        auth_header = generate_auth_header(scopes=[SYSTEM_CREATE])

        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_create_request_body.json(exclude_none=True),
        )

        assert result.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert result.json()["detail"][0]["loc"] == [
            "body",
            "legal_basis_for_profiling",
            0,
        ]


@pytest.mark.unit
class TestSystemGet:
    def test_data_stewards_included_in_response(
        self, test_config, system, system_manager
    ):
        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            resource_id=system.fides_key,
        )
        assert result.status_code == 200
        assert result.json()["fides_key"] == system.fides_key

        data_stewards = result.json()["data_stewards"]
        assert len(data_stewards) == 1
        steward = data_stewards[0]

        assert steward["id"] == system_manager.id
        assert steward["username"] == system_manager.username
        assert "first_name" in steward
        assert "last_name" in steward


@pytest.mark.unit
class TestSystemList:
    @pytest.fixture(scope="function", autouse=True)
    def remove_all_systems(self, db) -> None:
        """Remove any systems (and privacy declarations) before test execution for clean state"""
        for privacy_declaration in PrivacyDeclaration.all(db):
            privacy_declaration.delete(db)
        for system in System.all(db):
            system.delete(db)

    def test_list_no_pagination(self, test_config, system_with_cleanup):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
        )

        assert result.status_code == 200
        result_json = result.json()

        assert len(result_json) == 1
        assert result_json[0]["fides_key"] == system_with_cleanup.fides_key

    def test_list_with_pagination(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
            },
        )

        assert result.status_code == 200
        result_json = result.json()

        assert result_json["page"] == 1
        assert result_json["size"] == 5
        assert result_json["total"] == 2
        assert len(result_json["items"]) == 2

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == system_with_cleanup.fides_key
        assert sorted_items[1]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_default_page(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
    ):
        # We don't pass in the page but we pass in the size,
        # so we should get a paginated response with the default page number (1)
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "size": 5,
            },
        )

        assert result.status_code == 200
        result_json = result.json()

        assert result_json["page"] == 1
        assert result_json["size"] == 5
        assert result_json["total"] == 2
        assert len(result_json["items"]) == 2

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == system_with_cleanup.fides_key
        assert sorted_items[1]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_default_size(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
    ):
        # We don't pass in the size but we pass in the page,
        # so we should get a paginated response with the default size (50)
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
            },
        )

        assert result.status_code == 200
        result_json = result.json()

        assert result_json["page"] == 1
        assert result_json["size"] == 50
        assert result_json["total"] == 2
        assert len(result_json["items"]) == 2

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == system_with_cleanup.fides_key
        assert sorted_items[1]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_and_search(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
        system_third_party_sharing,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={"page": 1, "size": 5, "search": "tcf"},
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 1
        assert len(result_json["items"]) == 1
        assert result_json["items"][0]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_and_data_uses_filter(
        self,
        test_config,
        system_multiple_decs,
        tcf_system,
        system_third_party_sharing,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "data_uses": ["third_party_sharing"],
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 2
        assert len(result_json["items"]) == 2

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])

        assert sorted_items[0]["fides_key"] == system_multiple_decs.fides_key
        assert sorted_items[1]["fides_key"] == system_third_party_sharing.fides_key

    def test_list_with_pagination_and_multiple_data_uses_filter(
        self,
        test_config,
        system_multiple_decs,
        tcf_system,
        system_third_party_sharing,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "data_uses": ["third_party_sharing", "essential.fraud_detection"],
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 3
        assert len(result_json["items"]) == 3

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == system_multiple_decs.fides_key
        assert sorted_items[1]["fides_key"] == system_third_party_sharing.fides_key
        assert sorted_items[2]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_and_data_categories_filter(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
        system_third_party_sharing,
        system_with_no_uses,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "data_categories": ["user.device.cookie_id"],
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 3
        assert len(result_json["items"]) == 3

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == system_with_cleanup.fides_key
        assert sorted_items[1]["fides_key"] == system_third_party_sharing.fides_key
        assert sorted_items[2]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_and_data_subjects_filter(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
        system_third_party_sharing,
        system_with_no_uses,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "data_subjects": ["customer"],
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 3
        assert len(result_json["items"]) == 3

        sorted_items = sorted(result_json["items"], key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == system_with_cleanup.fides_key
        assert sorted_items[1]["fides_key"] == system_third_party_sharing.fides_key
        assert sorted_items[2]["fides_key"] == tcf_system.fides_key

    def test_list_with_pagination_and_multiple_filters(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
        system_third_party_sharing,
        system_with_no_uses,
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                # TCF System has different privacy declarations, that together have all these fields
                "data_uses": ["essential.fraud_detection"],
                "data_subjects": ["customer"],
                "data_categories": ["user"],
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 1
        assert len(result_json["items"]) == 1

        assert result_json["items"][0]["fides_key"] == tcf_system.fides_key

    def test_list_with_dnd_filter(
        self,
        test_config,
        system_with_cleanup,  # one that has a connection config
        system_third_party_sharing,  # one that doesn't have a connection config
    ):
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "dnd_relevant": "true",
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 1
        assert len(result_json["items"]) == 1

        # only "system_with_cleanup" has a connection config attached to it in fixtures
        assert result_json["items"][0]["fides_key"] == system_with_cleanup.fides_key

    def test_list_with_show_hidden(
        self,
        test_config,
        system_hidden,
        system_with_cleanup,
    ):

        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "show_hidden": "true",
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 2
        assert len(result_json["items"]) == 2

        actual_keys = [item["fides_key"] for item in result_json["items"]]
        assert system_hidden.fides_key in actual_keys
        assert system_with_cleanup.fides_key in actual_keys

        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                "show_hidden": "false",
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 1
        assert len(result_json["items"]) == 1

        assert result_json["items"][0]["fides_key"] == system_with_cleanup.fides_key

    @pytest.mark.skip("Until we re-visit filter implementation")
    def test_list_with_pagination_and_multiple_filters_2(
        self,
        test_config,
        system_with_cleanup,
        tcf_system,
        system_third_party_sharing,
        system_with_no_uses,
        db,
    ):

        db.que
        result = _api.ls(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type="system",
            query_params={
                "page": 1,
                "size": 5,
                # TCF system has a single privacy declaration with all these fields
                "data_uses": ["essential.fraud_detection"],
                "data_subjects": ["customer"],
                "data_categories": ["user.device.cookie_id"],
            },
        )

        assert result.status_code == 200
        result_json = result.json()
        assert result_json["total"] == 1
        assert len(result_json["items"]) == 1

        assert result_json["items"][0]["fides_key"] == tcf_system.fides_key


@pytest.mark.unit
class TestSystemUpdate:
    updated_system_name = "Updated System Name"

    @pytest.fixture(scope="function", autouse=True)
    def remove_all_systems(self, db) -> None:
        """Remove any systems (and privacy declarations) before test execution for clean state"""
        for privacy_declaration in PrivacyDeclaration.all(db):
            privacy_declaration.delete(db)
        for system in System.all(db):
            system.delete(db)

    @pytest.fixture(scope="function")
    def system_update_request_body(self, system) -> SystemSchema:
        return SystemSchema(
            organization_fides_key="1",
            fides_key=system.fides_key,
            system_type="SYSTEM",
            name=self.updated_system_name,
            vendor_deleted_date=datetime(2022, 5, 22),
            description="Test Policy",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=[],
                    ingress=None,
                    egress=None,
                )
            ],
        )

    @pytest.fixture(scope="function")
    def system_update_request_body_with_system_cookies(self, system) -> SystemSchema:
        return SystemSchema(
            organization_fides_key="1",
            fides_key=system.fides_key,
            system_type="SYSTEM",
            name=self.updated_system_name,
            description="Test Policy",
            cookies=[
                {"name": "my_system_cookie", "domain": "example.com"},
                {"name": "my_other_system_cookie"},
            ],
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=[],
                    ingress=None,
                    egress=None,
                )
            ],
        )

    @pytest.fixture(scope="function")
    def system_update_request_body_with_privacy_declaration_cookies(
        self, system
    ) -> SystemSchema:
        return SystemSchema(
            organization_fides_key="1",
            fides_key=system.fides_key,
            system_type="SYSTEM",
            name=self.updated_system_name,
            description="Test Policy",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=[],
                    cookies=[
                        {"name": "my_cookie", "domain": "example.com"},
                        {"name": "my_other_cookie"},
                    ],
                )
            ],
        )

    @pytest.fixture(scope="function")
    def system_update_request_body_with_new_dictionary_fields(
        self, system
    ) -> SystemSchema:
        return SystemSchema(
            organization_fides_key="1",
            fides_key=system.fides_key,
            system_type="SYSTEM",
            name=self.updated_system_name,
            description="Test Policy",
            vendor_id="test_vendor",
            dataset_references=["another_system_reference"],
            processes_personal_data=True,
            exempt_from_privacy_regulations=False,
            reason_for_exemption=None,
            uses_profiling=True,
            legal_basis_for_profiling=["Authorised by law", "Contract"],
            does_international_transfers=True,
            legal_basis_for_transfers=[
                "Adequacy Decision",
                "BCRs",
                "Supplementary Measures",
                "Unknown legal basis",
            ],
            requires_data_protection_assessments=True,
            dpa_location="https://www.example.com/dpa",
            dpa_progress="pending",
            privacy_policy="https://www.example.com/privacy_policy",
            legal_name="Sunshine Corporation",
            legal_address="35925 Test Lane, Test Town, TX 24924",
            responsibility=["Processor"],
            dpo="John Doe, CIPT",
            joint_controller_info="Jane Doe",
            data_security_practices="We encrypt all your data in transit and at rest",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=["another_system_reference"],
                    features=["Link different devices"],
                    legal_basis_for_processing="Public interest",
                    impact_assessment_location="https://www.example.com/impact_assessment_location",
                    retention_period="3-5 years",
                    processes_special_category_data=True,
                    special_category_legal_basis="Reasons of substantial public interest (with a basis in law)",
                    data_shared_with_third_parties=True,
                    third_parties="Third Party Marketing Dept.",
                    shared_categories=["user"],
                    cookies=[
                        {
                            "name": "essential_cookie",
                            "path": "/",
                            "domain": "example.com",
                        }
                    ],
                )
            ],
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
        assert system.vendor_deleted_date == datetime(2022, 5, 22, tzinfo=timezone.utc)

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
        assert result.json() == {
            "detail": "Invalid privacy declaration referencing unknown DataUse invalid_data_use"
        }

        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_use == "marketing.advertising"

    def test_system_update_privacy_declaration_invalid_data_category(
        self,
        system,
        test_config,
        system_update_request_body,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.privacy_declarations[0].data_categories = [
            "invalid_data_category"
        ]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": "Invalid privacy declaration referencing unknown DataCategory invalid_data_category"
        }
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_categories == [
            "user.device.cookie_id"
        ]

    def test_system_update_privacy_declaration_invalid_data_subject(
        self,
        system,
        test_config,
        system_update_request_body,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.privacy_declarations[0].data_subjects = [
            "invalid_data_subject"
        ]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": "Invalid privacy declaration referencing unknown DataSubject invalid_data_subject"
        }
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_subjects == ["customer"]

    def test_system_update_privacy_declaration_inactive_data_use(
        self,
        system,
        test_config,
        system_update_request_body,
        inactive_data_use,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.privacy_declarations[0].data_use = (
            inactive_data_use.fides_key
        )
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": f"Invalid privacy declaration referencing inactive DataUse {inactive_data_use.fides_key}"
        }
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_use == "marketing.advertising"

    def test_system_update_privacy_declaration_inactive_data_category(
        self,
        system,
        test_config,
        system_update_request_body,
        inactive_data_category,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.privacy_declarations[0].data_categories = [
            inactive_data_category.fides_key
        ]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": f"Invalid privacy declaration referencing inactive DataCategory {inactive_data_category.fides_key}"
        }
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_categories == [
            "user.device.cookie_id"
        ]

    def test_system_update_privacy_declaration_inactive_data_subject(
        self,
        system,
        test_config,
        system_update_request_body,
        inactive_data_subject,
        generate_role_header,
        db,
    ):
        auth_header = generate_role_header(roles=[OWNER])
        system_update_request_body.privacy_declarations[0].data_subjects = [
            inactive_data_subject.fides_key
        ]
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body.json(exclude_none=True),
        )
        assert result.status_code == HTTP_400_BAD_REQUEST
        assert result.json() == {
            "detail": f"Invalid privacy declaration referencing inactive DataSubject {inactive_data_subject.fides_key}"
        }
        # assert the system's privacy declaration has not been updated
        db.refresh(system)
        assert system.privacy_declarations[0].data_subjects == ["customer"]

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
                data_use="essential",  # same as initial PrivacyDeclaration
                data_subjects=["anonymous_user"],  # other fields can differ
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
        assert system.privacy_declarations[0].data_use == "marketing.advertising"

        # test that duplicate with no name on either declaration fails
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="",  # no name specified
                data_categories=["user.payment"],
                data_use="essential",  # identical data use
                data_subjects=["anonymous_user"],  # other fields can differ
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="",  # no name specified
                data_categories=["user.payment"],
                data_use="essential",  # identicial data use
                data_subjects=["anonymous_user"],
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
        assert system.privacy_declarations[0].data_use == "marketing.advertising"

        # test that duplicate data_use with no name on one declaration succeeds
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="",  # no name specified
                data_categories=["user.payment"],
                data_use="essential",  # identical data use
                data_subjects=["anonymous_user"],
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration",  # this name distinguishes the declaration from the above
                data_categories=["user.payment"],
                data_use="essential",  # identicial data use
                data_subjects=["anonymous_user"],
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
        assert system.privacy_declarations[0].data_use == "essential"
        assert system.privacy_declarations[1].data_use == "essential"

        # test that duplicate data_use with differeing names on declarations succeeds
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 1",  # specify a unique name here
                data_categories=["user.payment"],
                data_use="marketing.advertising",  # identical data use
                data_subjects=["anonymous_user"],
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 2",  # this name distinguishes the declaration from the above
                data_categories=["user.payment"],
                data_use="marketing.advertising",  # identicial data use
                data_subjects=["anonymous_user"],
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
        assert system.privacy_declarations[0].data_use == "marketing.advertising"
        assert system.privacy_declarations[1].data_use == "marketing.advertising"

        # test that differeing data_use with same names on declarations succeeds
        system_update_request_body.privacy_declarations = []
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 1",  # identical name
                data_categories=["user.payment"],
                data_use="marketing.advertising",  # differing data use
                data_subjects=["anonymous_user"],
                dataset_references=[],
            )
        )
        system_update_request_body.privacy_declarations.append(
            models.PrivacyDeclaration(
                name="new declaration 1",  # identical name
                data_categories=["user.payment"],
                data_use="essential",  # differing data use
                data_subjects=["anonymous_user"],
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
            system.privacy_declarations[0].data_use == "marketing.advertising"
            and system.privacy_declarations[1].data_use == "essential"
        ) or (
            system.privacy_declarations[1].data_use == "marketing.advertising"
            and system.privacy_declarations[0].data_use == "essential"
        )
        assert (
            system.privacy_declarations[0].name == "new declaration 1"
            and system.privacy_declarations[1].name == "new declaration 1"
        )

    def test_system_update_dictionary_fields(
        self,
        test_config,
        system_update_request_body_with_new_dictionary_fields,
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
            json_resource=system_update_request_body_with_new_dictionary_fields.json(
                exclude_none=True
            ),
        )

        assert result.status_code == HTTP_200_OK

        db.refresh(system)

        assert system.name == self.updated_system_name
        assert system.vendor_id == "test_vendor"
        assert system.dataset_references == ["another_system_reference"]
        assert system.processes_personal_data is True
        assert system.exempt_from_privacy_regulations is False
        assert system.reason_for_exemption is None
        assert system.uses_profiling is True
        assert system.legal_basis_for_profiling == ["Authorised by law", "Contract"]
        assert system.does_international_transfers is True
        assert system.legal_basis_for_transfers == [
            "Adequacy Decision",
            "BCRs",
            "Supplementary Measures",
            "Unknown legal basis",
        ]
        assert system.requires_data_protection_assessments is True
        assert system.dpa_location == "https://www.example.com/dpa"
        assert system.dpa_progress == "pending"
        assert system.privacy_policy == "https://www.example.com/privacy_policy"
        assert system.legal_name == "Sunshine Corporation"
        assert system.legal_address == "35925 Test Lane, Test Town, TX 24924"
        assert system.responsibility == ["Processor"]
        assert system.dpo == "John Doe, CIPT"
        assert system.joint_controller_info == "Jane Doe"
        assert (
            system.data_security_practices
            == "We encrypt all your data in transit and at rest"
        )
        assert system.data_stewards == []

        privacy_decl = system.privacy_declarations[0]
        assert privacy_decl.name == "declaration-name"
        assert privacy_decl.dataset_references == ["another_system_reference"]
        assert privacy_decl.features == ["Link different devices"]
        assert privacy_decl.legal_basis_for_processing == "Public interest"
        assert (
            privacy_decl.impact_assessment_location
            == "https://www.example.com/impact_assessment_location"
        )
        assert privacy_decl.retention_period == "3-5 years"
        assert privacy_decl.processes_special_category_data is True
        assert (
            privacy_decl.special_category_legal_basis
            == "Reasons of substantial public interest (with a basis in law)"
        )
        assert privacy_decl.data_shared_with_third_parties is True
        assert privacy_decl.third_parties == "Third Party Marketing Dept."
        assert privacy_decl.shared_categories == ["user"]

        json_results = result.json()
        for field in SystemResponse.model_fields:
            system_val = getattr(system, field)
            if isinstance(system_val, typing.Hashable) and not isinstance(
                system_val, datetime
            ):
                assert system_val == json_results[field]
        assert len(json_results["privacy_declarations"]) == 1
        assert json_results["data_stewards"] == []
        assert json_results["created_at"]

        for i, decl in enumerate(system.privacy_declarations):
            for field in PrivacyDeclarationResponse.model_fields:
                decl_val = getattr(decl, field, None)
                if hasattr(decl, field) and isinstance(decl_val, typing.Hashable):
                    assert decl_val == json_results["privacy_declarations"][i][field]

    def test_system_update_system_cookies(
        self,
        test_config,
        system_update_request_body_with_system_cookies,
        system,
        db,
        generate_system_manager_header,
    ):
        assert system.name != self.updated_system_name
        assert len(system.cookies) == 1

        auth_header = generate_system_manager_header([system.id])
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body_with_system_cookies.json(
                exclude_none=True
            ),
        )
        assert result.status_code == HTTP_200_OK
        assert result.json()["name"] == self.updated_system_name
        # System level cookies removed
        assert result.json()["cookies"] == [
            {"name": "my_system_cookie", "domain": "example.com", "path": None},
            {"name": "my_other_system_cookie", "domain": None, "path": None},
        ]

        # Privacy declaration cookies added
        assert result.json()["privacy_declarations"][0]["cookies"] == []

        db.refresh(system)
        assert system.name == self.updated_system_name
        assert len(system.cookies) == 2
        assert len(system.privacy_declarations[0].cookies) == 0

        system_history = (
            db.query(SystemHistory).filter(SystemHistory.system_id == system.id).first()
        )
        cookie_history = system_history.after["cookies"]
        assert {cookie["name"] for cookie in cookie_history} == {
            "my_system_cookie",
            "my_other_system_cookie",
        }

    def test_system_update_privacy_declaration_cookies(
        self,
        test_config,
        system_update_request_body_with_privacy_declaration_cookies,
        system,
        db,
        generate_system_manager_header,
    ):
        assert system.name != self.updated_system_name
        assert len(system.cookies) == 1

        auth_header = generate_system_manager_header([system.id])
        result = _api.update(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type="system",
            json_resource=system_update_request_body_with_privacy_declaration_cookies.json(
                exclude_none=True
            ),
        )
        assert result.status_code == HTTP_200_OK
        assert result.json()["name"] == self.updated_system_name
        # System level cookies removed
        assert result.json()["cookies"] == []
        # Privacy declaration cookies added
        assert sorted(
            result.json()["privacy_declarations"][0]["cookies"], key=lambda r: r["name"]
        ) == sorted(
            [
                {"name": "my_cookie", "path": None, "domain": "example.com"},
                {"name": "my_other_cookie", "path": None, "domain": None},
            ],
            key=lambda r: r["name"],
        )

        db.refresh(system)
        assert system.name == self.updated_system_name
        assert (
            len(system.cookies)
            == 0  # System cookies were deleted because they weren't in the request
        )  # Two from the current privacy declaration
        assert len(system.privacy_declarations[0].cookies) == 2

    @pytest.mark.parametrize(
        "update_declarations",
        [
            (
                [  # add a privacy declaration distinct from existing declaration
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="essential",
                        data_subjects=[],
                        dataset_references=[],
                        cookies=[],
                        egress=None,
                        ingress=None,
                    )
                ]
            ),
            (
                # add 2 privacy declarations distinct from existing declaration
                [
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="essential",
                        data_subjects=[],
                        dataset_references=[],
                        cookies=[],
                        egress=None,
                        ingress=None,
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        dataset_references=[],
                        cookies=[],
                        egress=None,
                        ingress=None,
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
                        dataset_references=[],
                        cookies=[],
                        ingress=None,
                        egress=None,
                    ),
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                        cookies=[],
                        ingress=None,
                        egress=None,
                    ),
                ]
            ),
            (
                # add 2 privacy declarations, one the same data use and name as existing, other same data use
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                        cookies=[],
                        egress=None,
                        ingress=None,
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                        cookies=[],
                        egress=None,
                        ingress=None,
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

        assert len(response_decs) == len(
            update_declarations
        ), "Response declaration count doesn't match the number sent!"
        for response_dec in response_decs:
            assert (
                "id" in response_dec.keys()
            ), "No 'id' field in the response declaration!"

            parsed_response_declaration = models.PrivacyDeclaration.model_validate(
                response_dec
            )
            assert (
                parsed_response_declaration in update_declarations
            ), "The response declaration '{}' doesn't match anything in the request declarations!".format(
                parsed_response_declaration.name
            )

        # do the same for the declarations in our db record
        system = System.all(db)[0]
        db.refresh(system)
        db_decs = [
            models.PrivacyDeclaration.model_validate(db_dec)
            for db_dec in system.privacy_declarations
        ]

        for update_dec in update_declarations:
            db_decs.remove(update_dec)
        # and assert we don't have any extra response declarations
        assert len(db_decs) == 0

    @pytest.mark.parametrize(
        "update_declarations",
        [
            (
                [  # Check 1: update a dec matching one existing dec
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    )
                ]
            ),
            (
                [  # Check 2: add a new single dec with same data use
                    models.PrivacyDeclaration(
                        name="declaration-name-1",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    )
                ]
            ),
            (
                [  # Check 3: add a new single dec with same data use, no name
                    models.PrivacyDeclaration(
                        name="",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    )
                ]
            ),
            (
                # Check 4: update 2 privacy declarations both matching existing decs
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="Collect data for third party sharing",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # Check 5: update 2 privacy declarations, one with matching name and data use, other only data use
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # Check 6: update 2 privacy declarations, one with matching name and data use, other only data use but same data use
                [
                    models.PrivacyDeclaration(
                        name="Collect data for marketing",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # Check 7: update 2 privacy declarations, one with only matching data use, other totally new
                [
                    models.PrivacyDeclaration(
                        name="declaration-name-1",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="essential",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # Check 8: add 2 new privacy declarations
                [
                    models.PrivacyDeclaration(
                        name="declaration-name",
                        data_categories=[],
                        data_use="essential",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="declaration-name-2",
                        data_categories=[],
                        data_use="functional",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # Check 9: add 2 new privacy declarations, same data uses as existing decs but no names
                [
                    models.PrivacyDeclaration(
                        name="",
                        data_categories=[],
                        data_use="marketing.advertising",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                    models.PrivacyDeclaration(
                        name="",
                        data_categories=[],
                        data_use="third_party_sharing",
                        data_subjects=[],
                        dataset_references=[],
                    ),
                ]
            ),
            (
                # Check 10: specify no declarations, declarations should be cleared off the system
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
            PrivacyDeclarationResponse.model_validate(dec)
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
        updated_decs: List[PrivacyDeclaration] = (
            system_multiple_decs.privacy_declarations.copy()
        )

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
        assert result.status_code == HTTP_403_FORBIDDEN

    def test_delete_system_deletes_connection_config_and_dataset(
        self,
        test_config,
        db,
        system,
        generate_auth_header,
        dataset_config: DatasetConfig,
    ) -> None:
        """
        Ensure that deleting the system also deletes any associated
        ConnectionConfig and DatasetConfig records
        """
        auth_header = generate_auth_header(scopes=[SYSTEM_DELETE])

        connection_config = dataset_config.connection_config
        connection_config.system_id = (
            system.id
        )  # tie the connectionconfig to the system we will delete
        connection_config.save(db)
        # the keys are cached before the delete
        connection_config_key = connection_config.key
        dataset_config_key = dataset_config.fides_key

        # delete the system via API
        result = _api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=auth_header,
        )
        assert result.status_code == HTTP_200_OK

        # ensure our system itself was deleted
        assert db.query(System).filter_by(fides_key=system.fides_key).first() is None
        # ensure our associated ConnectionConfig was deleted
        assert (
            db.query(ConnectionConfig).filter_by(key=connection_config_key).first()
            is None
        )
        # and ensure our associated DatasetConfig was deleted
        assert (
            db.query(DatasetConfig).filter_by(fides_key=dataset_config_key).first()
            is None
        )

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
        assert (
            "cannot modify a resource where 'is_default' is true"
            in result.json()["detail"]["error"]
        )

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
        resources = [
            r.model_dump(mode="json") for r in getattr(DEFAULT_TAXONOMY, endpoint)[0:2]
        ]
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

        #  Set fields for default labels
        manifest.is_default = True
        manifest.version_added = "2.0.0"

        result = _api.create(
            url=test_config.cli.server_url,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
            headers=test_config.user.auth_header,
        )
        assert result.status_code == 403
        assert (
            "cannot create a resource where 'is_default' is true"
            in result.json()["detail"]["error"]
        )

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

        #  Set fields for default labels
        manifest.is_default = True
        manifest.version_added = "2.0.0"

        result = _api.upsert(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resources=[manifest.model_dump(mode="json")],
        )
        assert result.status_code == 403
        assert (
            "cannot create a resource where 'is_default' is true"
            in result.json()["detail"]["error"]
        )

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

        #  Set fields for default labels
        manifest.is_default = True
        manifest.version_added = "2.0.0"

        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            json_resource=manifest.json(exclude_none=True),
        )
        assert result.status_code == 403
        assert (
            "cannot modify 'is_default' field on an existing resource"
            in result.json()["detail"]["error"]
        )

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_cannot_upsert_is_default(
        self, test_config: FidesConfig, resources_dict: Dict, endpoint: str
    ) -> None:
        manifest = resources_dict[endpoint]
        second_item = manifest.model_copy()

        #  Set fields for default labels
        manifest.is_default = True
        manifest.version_added = "2.0.0"

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
            resources=[
                manifest.model_dump(mode="json"),
                second_item.model_dump(mode="json"),
            ],
        )
        assert result.status_code == 403
        assert (
            "cannot modify 'is_default' field on an existing resource"
            in result.json()["detail"]["error"]
        )

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
class TestCrudActiveProperty:
    """
    Ensure `active` property is exposed properly via CRUD endpoints.
    Specific tests for this property since it's a fides-specific
    extension to the underlying fideslang taxonomy models.
    """

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_can_update_active_on_default(
        self, test_config: FidesConfig, endpoint: str
    ) -> None:
        """Ensure we can toggle `active` property on default taxonomy elements"""
        resource = getattr(DEFAULT_TAXONOMY, endpoint)[0]
        resource = TAXONOMY_EXTENSIONS[endpoint](
            **resource.model_dump(mode="json")
        )  # cast resource to extended model
        resource.active = False
        json_resource = resource.json(exclude_none=True)
        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            json_resource=json_resource,
        )
        assert result.status_code == 200
        assert result.json()["active"] is False

        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resource_id=resource.fides_key,
        )
        assert result.json()["active"] is False

        resource.active = True
        json_resource = resource.json(exclude_none=True)
        result = _api.update(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            json_resource=json_resource,
        )
        assert result.status_code == 200
        assert result.json()["active"] is True

        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resource_id=resource.fides_key,
        )
        assert result.json()["active"] is True

    @pytest.mark.parametrize("endpoint", TAXONOMY_ENDPOINTS)
    def test_api_can_create_with_active_property(
        self,
        test_config: FidesConfig,
        endpoint: str,
        generate_auth_header,
    ) -> None:
        """Ensure we can create taxonomy elements with `active` property set"""
        # get a default taxonomy element as a sample resource
        resource = getattr(DEFAULT_TAXONOMY, endpoint)[0]
        resource = TAXONOMY_EXTENSIONS[endpoint](
            **resource.model_dump(mode="json")
        )  # cast resource to extended model
        resource.fides_key = resource.fides_key + "_test_create_active_false"
        resource.is_default = False
        resource.version_added = None
        resource.active = False
        json_resource = resource.json(exclude_none=True)
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{CREATE}"]
        auth_header = generate_auth_header(scopes=token_scopes)
        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            json_resource=json_resource,
        )
        assert result.status_code == 201
        assert result.json()["active"] is False

        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resource_id=resource.fides_key,
        )
        assert result.json()["active"] is False

        resource.fides_key = resource.fides_key + "_test_create_active_true"
        resource.active = True
        json_resource = resource.json(exclude_none=True)
        token_scopes: List[str] = [f"{CLI_SCOPE_PREFIX_MAPPING[endpoint]}:{CREATE}"]
        auth_header = generate_auth_header(scopes=token_scopes)
        result = _api.create(
            url=test_config.cli.server_url,
            headers=auth_header,
            resource_type=endpoint,
            json_resource=json_resource,
        )
        assert result.status_code == 201
        assert result.json()["active"] is True

        result = _api.get(
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            resource_type=endpoint,
            resource_id=resource.fides_key,
        )
        assert result.json()["active"] is True


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
class TestHealthchecks:
    @pytest.mark.parametrize(
        "database_health, expected_status_code",
        [("healthy", 200), ("unhealthy", 503), ("needs migration", 503)],
    )
    def test_database_healthcheck(
        self,
        test_config: FidesConfig,
        database_health: str,
        expected_status_code: int,
        monkeypatch: MonkeyPatch,
        test_client: TestClient,
    ) -> None:
        """Test the database health checks."""

        def mock_get_db_health(url: str, db) -> Tuple[str, str]:
            return (
                database_health,
                "9e83545ed9b6",
            )  # just an arbitrary revision # for testing

        monkeypatch.setattr(health, "get_db_health", mock_get_db_health)
        response = test_client.get(test_config.cli.server_url + "/health/database")
        assert (
            response.status_code == expected_status_code
        ), f"Request failed: {response.text}"

    def test_server_healthcheck(
        self,
        test_config: FidesConfig,
        test_client: TestClient,
    ) -> None:
        """Test the server healthcheck."""
        response = test_client.get(test_config.cli.server_url + "/health")
        assert response.status_code == 200

    def test_worker_healthcheck(
        self,
        test_config: FidesConfig,
        test_client: TestClient,
    ) -> None:
        """Test the server healthcheck."""
        response = test_client.get(test_config.cli.server_url + "/health/workers")
        assert response.status_code == 200
        assert response.json() == {
            "workers_enabled": False,
            "workers": [],
            "queue_counts": {},
        }

    @pytest.mark.usefixtures("enable_celery_worker")
    def test_worker_health_check_with_workers_enabled(self, test_config, test_client):
        response = test_client.get(test_config.cli.server_url + "/health/workers")
        assert response.status_code == 200
        # Workers not actually running in pytest though
        assert response.json() == {
            "workers_enabled": True,
            "workers": [],
            "queue_counts": {
                "fidesops.messaging": 0,
                "fides.privacy_preferences": 0,
                "fides": 0,
            },
        }


@pytest.mark.integration
@pytest.mark.parametrize("endpoint_name", [f"{API_PREFIX}/organization", "/health"])
def test_trailing_slash(test_config: FidesConfig, endpoint_name: str) -> None:
    """URLs both with and without a trailing slash should resolve and not 404"""
    url = f"{test_config.cli.server_url}{endpoint_name}"
    response = requests.get(url, headers=CONFIG.user.auth_header)
    assert response.status_code == 200
    response = requests.get(f"{url}/", headers=CONFIG.user.auth_header)
    assert response.status_code == 200


class TestPrivacyDeclarationGetPurposeLegalBasisOverride:
    async def test_privacy_declaration_enable_override_is_false(
        self, async_session_temp
    ):
        """Enable override is false so overridden legal basis is going to default
        to the defined legal basis"""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="analytics.reporting.campaign_insights",
                    legal_basis_for_processing="Consent",
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        pd = system.privacy_declarations[0]

        assert pd.purpose == 9
        assert await pd.get_purpose_legal_basis_override() == "Consent"

    @pytest.mark.usefixtures(
        "enable_override_vendor_purposes",
    )
    async def test_enable_override_is_true_but_no_matching_purpose(
        self, async_session_temp, db
    ):
        """Privacy Declaration has Special Purpose not Purpose, so no overrides applicable"""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="essential.fraud_detection",
                    legal_basis_for_processing="Consent",
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        pd = system.privacy_declarations[0]

        assert pd.purpose is None
        assert await pd.get_purpose_legal_basis_override() == "Consent"

    @pytest.mark.usefixtures(
        "enable_override_vendor_purposes",
    )
    async def test_enable_override_is_true_but_purpose_is_excluded(
        self, async_session_temp, db
    ):
        """Purpose is overridden as excluded, so legal basis returns as None, to match
        class-wide override"""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="personalize.content.profiling",
                    legal_basis_for_processing="Consent",
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        pd = system.privacy_declarations[0]

        constraint = TCFPurposeOverride.create(
            db,
            data={
                "purpose": 5,
                "is_included": False,
            },
        )

        assert pd.purpose == 5
        assert await pd.get_purpose_legal_basis_override() is None

        constraint.delete(db)

    @pytest.mark.usefixtures(
        "enable_override_vendor_purposes",
    )
    async def test_purpose_is_excluded_even_with_inflexible_legal_basis(
        self, async_session_temp, db
    ):
        """Purpose is overridden as excluded, so even if legal basis is not flexible,
        legal basis returns as None, to match class-wide override."""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="personalize.content.profiling",
                    legal_basis_for_processing="Consent",
                    flexible_legal_basis_for_processing=False,
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        pd = system.privacy_declarations[0]

        constraint = TCFPurposeOverride.create(
            db,
            data={
                "purpose": 5,
                "is_included": False,
            },
        )

        assert pd.purpose == 5
        assert await pd.get_purpose_legal_basis_override() is None

        constraint.delete(db)

    @pytest.mark.usefixtures(
        "enable_override_vendor_purposes",
    )
    async def test_legal_basis_is_inflexible(self, async_session_temp, db):
        """Purpose is overridden but we can't apply because the legal basis is specified as inflexible"""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="personalize.content.profiling",
                    legal_basis_for_processing="Consent",
                    flexible_legal_basis_for_processing=False,
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        pd = system.privacy_declarations[0]

        constraint = TCFPurposeOverride.create(
            db,
            data={
                "purpose": 5,
                "is_included": True,
                "required_legal_basis": "Legitimate interests",
            },
        )

        assert pd.purpose == 5
        assert await pd.get_purpose_legal_basis_override() == "Consent"

        constraint.delete(db)

    @pytest.mark.usefixtures(
        "enable_override_vendor_purposes",
    )
    async def test_publisher_override_defined_but_no_required_legal_basis_specified(
        self, db, async_session_temp
    ):
        """Purpose override *object* is defined, but no legal basis override"""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="analytics.reporting.campaign_insights",
                    legal_basis_for_processing="Consent",
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        pd = system.privacy_declarations[0]

        constraint = TCFPurposeOverride.create(
            db,
            data={
                "purpose": 9,
                "is_included": True,
            },
        )

        assert pd.purpose == 9
        assert await pd.get_purpose_legal_basis_override() == "Consent"

        constraint.delete(db)

    @pytest.mark.usefixtures(
        "enable_override_vendor_purposes",
    )
    async def test_publisher_override_defined_with_required_legal_basis_specified(
        self, async_session_temp, db
    ):
        """Purpose override specified along with the requirements to apply that override"""
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name=f"test_system_1_{uuid4()}",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="Collect data for content performance",
                    data_use="functional.service.improve",
                    legal_basis_for_processing="Consent",
                    data_categories=["user"],
                )
            ],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        override = TCFPurposeOverride.create(
            db,
            data={
                "purpose": 10,
                "is_included": True,
                "required_legal_basis": "Legitimate interests",
            },
        )
        pd = system.privacy_declarations[0]

        assert pd.purpose == 10
        assert await pd.get_purpose_legal_basis_override() == "Legitimate interests"

        override.delete(db)
