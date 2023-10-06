# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Generator, List
from uuid import uuid4

import pytest
from fideslang.models import PrivacyDeclaration as PrivacyDeclarationSchema
from fideslang.models import System, SystemMetadata
from py._path.local import LocalPath
from sqlalchemy import delete

from fides.api.db.system import create_system, upsert_cookies
from fides.api.models.sql_models import Cookies, PrivacyDeclaration
from fides.api.models.sql_models import System as sql_System
from fides.config import FidesConfig
from fides.connectors.models import OktaConfig
from fides.core import api
from fides.core import system as _system


def create_server_systems(test_config: FidesConfig, systems: List[System]) -> None:
    for system in systems:
        api.create(
            url=test_config.cli.server_url,
            resource_type="system",
            json_resource=system.json(exclude_none=True),
            headers=test_config.user.auth_header,
        )


def delete_server_systems(test_config: FidesConfig, systems: List[System]) -> None:
    for system in systems:
        api.delete(
            url=test_config.cli.server_url,
            resource_type="system",
            resource_id=system.fides_key,
            headers=test_config.user.auth_header,
        )


def test_get_system_data_uses(db, system) -> None:
    assert sql_System.get_data_uses([system]) == {"marketing", "marketing.advertising"}

    system.privacy_declarations[0].update(
        db=db, data={"data_use": "marketing.advertising.first_party"}
    )

    assert sql_System.get_data_uses([system]) == {
        "marketing",
        "marketing.advertising",
        "marketing.advertising.first_party",
    }
    assert sql_System.get_data_uses([system], include_parents=False) == {
        "marketing.advertising.first_party"
    }

    system.privacy_declarations[0].delete(db)
    db.refresh(system)
    assert sql_System.get_data_uses([system]) == set()


@pytest.fixture(scope="function")
def create_test_server_systems(
    test_config: FidesConfig, redshift_systems: List[System]
) -> Generator:
    systems = redshift_systems
    delete_server_systems(test_config, systems)
    create_server_systems(test_config, systems)
    yield
    delete_server_systems(test_config, systems)


@pytest.fixture(scope="function")
def create_external_server_systems(test_config: FidesConfig) -> Generator:
    systems = (
        _system.generate_redshift_systems(
            organization_key="default_organization",
            aws_config={},
        )
        + _system.generate_rds_systems(
            organization_key="default_organization",
            aws_config={},
        )
        + _system.generate_resource_tagging_systems(
            organization_key="default_organization",
            aws_config={},
        )
    )
    delete_server_systems(test_config, systems)
    create_server_systems(test_config, systems)
    yield
    delete_server_systems(test_config, systems)


@pytest.fixture()
def redshift_describe_clusters() -> Generator:
    describe_clusters = {
        "Clusters": [
            {
                "ClusterIdentifier": "redshift-cluster-1",
                "Endpoint": {
                    "Address": "redshift-cluster-1.cue8hjdl1kb1.us-east-1.redshift.amazonaws.com",
                    "Port": 5439,
                },
                "ClusterNamespaceArn": "arn:aws:redshift:us-east-1:469973866127:namespace:5eb1f195-7815-4c62-9140-e062dd98da83",
            },
            {
                "ClusterIdentifier": "redshift-cluster-2",
                "Endpoint": {
                    "Address": "redshift-cluster-2.cue8hjdl1kb1.us-east-1.redshift.amazonaws.com",
                    "Port": 5439,
                },
                "ClusterNamespaceArn": "arn:aws:redshift:us-east-1:469973866127:namespace:06ba7fe3-8cb3-4e1c-b2c6-cc2f2415a979",
            },
        ]
    }
    yield describe_clusters


@pytest.fixture()
def redshift_systems() -> Generator:
    redshift_systems = [
        System.construct(
            fides_key="redshift-cluster-1",
            organization_fides_key="default_organization",
            name="redshift-cluster-1",
            description="Fides Generated Description for Redshift Cluster: redshift-cluster-1",
            fidesctl_meta=SystemMetadata(
                endpoint_address="redshift-cluster-1.cue8hjdl1kb1.us-east-1.redshift.amazonaws.com",
                endpoint_port="5439",
                resource_id="arn:aws:redshift:us-east-1:469973866127:namespace:5eb1f195-7815-4c62-9140-e062dd98da83",
            ),
            system_type="redshift_cluster",
            privacy_declarations=[],
        ),
        System.construct(
            fides_key="redshift-cluster-2",
            organization_fides_key="default_organization",
            name="redshift-cluster-2",
            description="Fides Generated Description for Redshift Cluster: redshift-cluster-2",
            fidesctl_meta=SystemMetadata(
                endpoint_address="redshift-cluster-2.cue8hjdl1kb1.us-east-1.redshift.amazonaws.com",
                endpoint_port="5439",
                resource_id="arn:aws:redshift:us-east-1:469973866127:namespace:06ba7fe3-8cb3-4e1c-b2c6-cc2f2415a979",
            ),
            system_type="redshift_cluster",
            privacy_declarations=[],
        ),
    ]
    yield redshift_systems


@pytest.fixture()
def rds_systems() -> Generator:
    rds_systems = [
        System(
            fides_key="database-2",
            organization_fides_key="default_organization",
            name="database-2",
            description="Fides Generated Description for RDS Cluster: database-2",
            fidesctl_meta=SystemMetadata(
                endpoint_address="database-2.cluster-ckrdpkkb4ukm.us-east-1.rds.amazonaws.com",
                endpoint_port="3306",
                resource_id="arn:aws:rds:us-east-1:910934740016:cluster:database-2",
            ),
            system_type="rds_cluster",
            privacy_declarations=[],
        ),
        System(
            fides_key="database-1",
            organization_fides_key="default_organization",
            name="database-1",
            description="Fides Generated Description for RDS Instance: database-1",
            fidesctl_meta=SystemMetadata(
                endpoint_address="database-1.ckrdpkkb4ukm.us-east-1.rds.amazonaws.com",
                endpoint_port="3306",
                resource_id="arn:aws:rds:us-east-1:910934740016:db:database-1",
            ),
            system_type="rds_instance",
            privacy_declarations=[],
        ),
    ]
    yield rds_systems


@pytest.fixture()
def rds_describe_clusters() -> Generator:
    describe_clusters = {
        "DBClusters": [
            {
                "DBClusterIdentifier": "database-2",
                "Endpoint": "database-2.cluster-cjh1qplnnv3b.us-east-1.rds.amazonaws.com",
                "Port": 3306,
                "DBClusterArn": "arn:aws:rds:us-east-1:469973866127:cluster:database-2",
            },
        ]
    }
    yield describe_clusters


@pytest.fixture()
def rds_describe_instances() -> Generator:
    describe_instances = {
        "DBInstances": [
            {
                "DBInstanceIdentifier": "database-1",
                "Endpoint": {
                    "Address": "database-1.cjh1qplnnv3b.us-east-1.rds.amazonaws.com",
                    "Port": 3306,
                },
                "DBInstanceArn": "arn:aws:rds:us-east-1:469973866127:db:database-1",
            },
        ]
    }
    yield describe_instances


@pytest.mark.integration
def test_get_all_server_systems(
    test_config: FidesConfig, create_test_server_systems: Generator
) -> None:
    actual_result = _system.get_all_server_systems(
        url=test_config.cli.server_url,
        headers=test_config.user.auth_header,
        exclude_systems=[],
    )
    assert actual_result


class TestSystemAWS:
    @pytest.mark.unit
    def test_get_system_resource_ids(self, redshift_systems: List[System]) -> None:
        expected_result = [
            "arn:aws:redshift:us-east-1:469973866127:namespace:5eb1f195-7815-4c62-9140-e062dd98da83",
            "arn:aws:redshift:us-east-1:469973866127:namespace:06ba7fe3-8cb3-4e1c-b2c6-cc2f2415a979",
        ]
        actual_result = _system.get_system_resource_ids(redshift_systems)
        assert actual_result == expected_result

    @pytest.mark.unit
    def test_find_missing_systems(
        self, redshift_systems: List[System], rds_systems: List[System]
    ) -> None:
        source_systems = rds_systems + redshift_systems
        existing_systems = redshift_systems
        actual_result = _system.find_missing_systems(
            source_systems=source_systems, existing_systems=existing_systems
        )
        assert actual_result == rds_systems

    @pytest.mark.external
    def test_scan_system_aws_passes(
        self, test_config: FidesConfig, create_external_server_systems: Generator
    ) -> None:
        _system.scan_system_aws(
            coverage_threshold=100,
            manifest_dir="",
            organization_key="default_organization",
            aws_config=None,
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
        )

    @pytest.mark.external
    def test_generate_system_aws(
        self, tmpdir: LocalPath, test_config: FidesConfig
    ) -> None:
        actual_result = _system.generate_system_aws(
            file_name=f"{tmpdir}/test_file.yml",
            include_null=False,
            organization_key="default_organization",
            aws_config=None,
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
        )
        assert actual_result


OKTA_ORG_URL = "https://dev-78908748.okta.com"


class TestSystemOkta:
    @pytest.mark.external
    def test_generate_system_okta(
        self, tmpdir: LocalPath, test_config: FidesConfig
    ) -> None:
        actual_result = _system.generate_system_okta(
            file_name=f"{tmpdir}/test_file.yml",
            include_null=False,
            organization_key="default_organization",
            okta_config=OktaConfig(
                orgUrl=OKTA_ORG_URL,
                token=os.environ["OKTA_CLIENT_TOKEN"],
            ),
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
        )
        assert actual_result

    @pytest.mark.external
    def test_scan_system_okta_success(
        self, tmpdir: LocalPath, test_config: FidesConfig
    ) -> None:
        file_name = f"{tmpdir}/test_file.yml"
        _system.generate_system_okta(
            file_name=file_name,
            include_null=False,
            organization_key="default_organization",
            okta_config=OktaConfig(
                orgUrl=OKTA_ORG_URL,
                token=os.environ["OKTA_CLIENT_TOKEN"],
            ),
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
        )
        _system.scan_system_okta(
            manifest_dir=file_name,
            okta_config=OktaConfig(
                orgUrl=OKTA_ORG_URL,
                token=os.environ["OKTA_CLIENT_TOKEN"],
            ),
            organization_key="default_organization",
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
        )
        assert True

    @pytest.mark.external
    def test_scan_system_okta_fail(
        self, tmpdir: LocalPath, test_config: FidesConfig
    ) -> None:
        with pytest.raises(SystemExit):
            _system.scan_system_okta(
                manifest_dir="",
                okta_config=OktaConfig(
                    orgUrl=OKTA_ORG_URL,
                    token=os.environ["OKTA_CLIENT_TOKEN"],
                ),
                coverage_threshold=100,
                organization_key="default_organization",
                url=test_config.cli.server_url,
                headers=test_config.user.auth_header,
            )


class TestUpsertCookies:
    @pytest.fixture()
    async def test_cookie_system(
        self,
        async_session_temp,
        generate_auth_header,
        test_config,
        generate_role_header,
        db,
    ):
        resource = System(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name="test_system_1",
            system_type="test",
            privacy_declarations=[
                PrivacyDeclarationSchema(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=[],
                ),
                PrivacyDeclarationSchema(
                    name="declaration-name-2",
                    data_categories=[],
                    data_use="functional.service.improve",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=[],
                ),
            ],
        )

        system = await create_system(resource, async_session_temp)

        Cookies.create(
            db=db,
            data={
                "name": "strawberry",
                "path": "/",
                "privacy_declaration_id": sorted(
                    system.privacy_declarations, key=lambda x: x.name
                )[1].id,
                "system_id": system.id,
            },
            check_name=False,
        )
        await async_session_temp.refresh(system)
        yield system
        delete(sql_System).where(sql_System.id == system.id)

    async def test_new_cookies(self, test_cookie_system, async_session_temp):
        """Test adding a new cookie to a privacy declaration.  The other privacy declaration on the
        system already has a cookie."""

        new_cookies = [{"name": "apple"}]
        privacy_declaration = sorted(
            test_cookie_system.privacy_declarations, key=lambda x: x.name
        )[0]

        await upsert_cookies(
            async_session_temp,
            new_cookies,
            privacy_declaration,
            test_cookie_system,
        )
        await async_session_temp.refresh(test_cookie_system)
        assert len(test_cookie_system.cookies) == 2

        assert {cookie.name for cookie in test_cookie_system.cookies} == {
            "strawberry",
            "apple",
        }
        assert len(privacy_declaration.cookies) == 1
        assert privacy_declaration.cookies[0].name == "apple"

        new_cookie = privacy_declaration.cookies[0]
        assert new_cookie.created_at is not None
        assert new_cookie.updated_at is not None
        assert new_cookie.name == "apple"
        assert new_cookie.system_id == test_cookie_system.id
        assert new_cookie.privacy_declaration_id == privacy_declaration.id

    async def test_no_change_to_cookies(self, test_cookie_system, async_session_temp):
        """Test specified cookies already exist on given privacy declaration, so no change required"""
        new_cookies = [{"name": "strawberry"}]
        privacy_declaration = sorted(
            test_cookie_system.privacy_declarations, key=lambda x: x.name
        )[1]
        existing_cookie = privacy_declaration.cookies[0]
        assert existing_cookie.name == "strawberry"

        await upsert_cookies(
            async_session_temp,
            new_cookies,
            privacy_declaration,
            test_cookie_system,
        )
        await async_session_temp.refresh(test_cookie_system)
        assert len(test_cookie_system.cookies) == 1

        assert {cookie.name for cookie in test_cookie_system.cookies} == {
            "strawberry",
        }
        assert len(privacy_declaration.cookies) == 1
        assert privacy_declaration.cookies[0].name == "strawberry"

        new_cookie = privacy_declaration.cookies[0]
        assert new_cookie.created_at is not None
        assert new_cookie.updated_at is not None
        assert new_cookie.name == "strawberry"
        assert new_cookie.system_id == test_cookie_system.id
        assert new_cookie.privacy_declaration_id == privacy_declaration.id

    async def test_update_cookies(self, test_cookie_system, async_session_temp):
        """Test cookie exists but path has changed"""
        """Test specified cookies already exist on given privacy declaration, so no change required"""

        new_cookies = [{"name": "strawberry", "path": "/"}]
        privacy_declaration = sorted(
            test_cookie_system.privacy_declarations, key=lambda x: x.name
        )[1]
        existing_cookie = privacy_declaration.cookies[0]
        assert existing_cookie.name == "strawberry"

        await upsert_cookies(
            async_session_temp,
            new_cookies,
            privacy_declaration,
            test_cookie_system,
        )
        await async_session_temp.refresh(test_cookie_system)
        assert len(test_cookie_system.cookies) == 1
        assert test_cookie_system.cookies[0].name == "strawberry"
        assert test_cookie_system.cookies[0].path == "/"

        assert len(privacy_declaration.cookies) == 1
        assert privacy_declaration.cookies[0].name == "strawberry"
        assert privacy_declaration.cookies[0].path == "/"

        new_cookie = privacy_declaration.cookies[0]
        assert new_cookie.created_at is not None
        assert new_cookie.updated_at is not None
        assert new_cookie.name == "strawberry"
        assert new_cookie.system_id == test_cookie_system.id
        assert new_cookie.privacy_declaration_id == privacy_declaration.id

    async def test_remove_cookies(self, test_cookie_system, async_session_temp):
        """Test cookie list is missing a cookie currently on the privacy declaration so add the new
        cookie and we remove the existing one"""

        new_cookies = [{"name": "apple"}]
        privacy_declaration = sorted(
            test_cookie_system.privacy_declarations, key=lambda x: x.name
        )[1]
        existing_cookie = privacy_declaration.cookies[0]
        assert existing_cookie.name == "strawberry"

        await upsert_cookies(
            async_session_temp,
            new_cookies,
            privacy_declaration,
            test_cookie_system,
        )
        await async_session_temp.refresh(test_cookie_system)
        assert len(test_cookie_system.cookies) == 1

        assert {cookie.name for cookie in test_cookie_system.cookies} == {
            "apple",
        }
        assert len(privacy_declaration.cookies) == 1
        assert privacy_declaration.cookies[0].name == "apple"

        new_cookie = privacy_declaration.cookies[0]
        assert new_cookie.created_at is not None
        assert new_cookie.updated_at is not None
        assert new_cookie.name == "apple"
        assert new_cookie.system_id == test_cookie_system.id
        assert new_cookie.privacy_declaration_id == privacy_declaration.id

    async def test_delete_privacy_declaration(
        self, test_cookie_system, async_session_temp
    ):
        """Test if a privacy declaration is deleted, its cookie is still linked to the system"""

        privacy_declaration = sorted(
            test_cookie_system.privacy_declarations, key=lambda x: x.name
        )[1]
        existing_cookie = privacy_declaration.cookies[0]

        assert existing_cookie.privacy_declaration_id == privacy_declaration.id
        assert existing_cookie.system_id == test_cookie_system.id

        stmt = delete(PrivacyDeclaration).where(
            PrivacyDeclaration.id == privacy_declaration.id
        )
        await async_session_temp.execute(stmt)
        await async_session_temp.refresh(existing_cookie)

        assert existing_cookie.privacy_declaration_id is None
        assert existing_cookie.system_id == test_cookie_system.id
