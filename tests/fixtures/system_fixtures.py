from typing import Generator
from uuid import uuid4

import pytest
from fideslang.models import System as SystemSchema
from sqlalchemy.orm import Session

from fides.api.db.system import create_system
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.sql_models import (
    Dataset as CtlDataset,
)
from fides.api.models.sql_models import (
    PrivacyDeclaration,
    System,
)
from fides.config import get_config

CONFIG = get_config()


@pytest.fixture(scope="function")
def system(db: Session) -> System:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for marketing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "marketing.advertising",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )

    db.refresh(system)
    return system


@pytest.fixture()
@pytest.mark.asyncio
async def system_async(async_session):
    """Creates a system for testing with an async session, to be used in async tests"""
    resource = SystemSchema(
        fides_key=str(uuid4()),
        organization_fides_key="default_organization",
        name="test_system_1",
        system_type="test",
        privacy_declarations=[],
    )

    system = await create_system(
        resource, async_session, CONFIG.security.oauth_root_client_id
    )
    return system


@pytest.fixture(scope="function")
def system_hidden(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system set as hidden",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "hidden": True,
        },
    )

    db.refresh(system)
    yield system
    db.delete(system)


@pytest.fixture(scope="function")
def system_with_cleanup(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for marketing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "marketing.advertising",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )

    ConnectionConfig.create(
        db=db,
        data={
            "system_id": system.id,
            "connection_type": "bigquery",
            "name": "test_connection",
            "secrets": {"password": "test_password"},
            "access": "write",
        },
    )

    db.refresh(system)
    yield system
    db.delete(system)


@pytest.fixture(scope="function")
def system_with_dataset_references(db: Session) -> System:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db, {"fides_key": f"dataset_key-f{uuid4()}", "collections": []}
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "dataset_references": [ctl_dataset.fides_key],
        },
    )

    return system


@pytest.fixture(scope="function")
def system_with_undeclared_data_categories(db: Session) -> System:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {"name": "first_name"},
                    ],
                }
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "dataset_references": [ctl_dataset.fides_key],
        },
    )

    return system


@pytest.fixture(scope="function")
def system_with_a_single_dataset_reference(db: Session) -> System:
    first_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "loyalty",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                }
            ],
        },
    )
    second_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "shipping_info",
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": ["user.contact.address.street"],
                                }
                            ],
                        },
                        {
                            "name": "first_name",
                            "data_categories": ["user.name.first"],
                        },
                    ],
                },
                {
                    "name": "activity",
                    "fields": [
                        {
                            "name": "last_login",
                            "data_categories": ["user.behavior"],
                        },
                    ],
                },
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "dataset_references": [first_dataset.fides_key, second_dataset.fides_key],
        },
    )

    return system


@pytest.fixture(scope="function")
def privacy_declaration_with_single_dataset_reference(
    db: Session,
) -> PrivacyDeclaration:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {"name": "first_name"},
                    ],
                }
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": [ctl_dataset.fides_key],
            "egress": None,
            "ingress": None,
        },
    )

    return privacy_declaration


@pytest.fixture(scope="function")
def privacy_declaration_with_multiple_dataset_references(
    db: Session,
) -> PrivacyDeclaration:
    first_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "loyalty",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                }
            ],
        },
    )
    second_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "shipping_info",
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": ["user.contact.address.street"],
                                }
                            ],
                        },
                        {
                            "name": "first_name",
                            "data_categories": ["user.name.first"],
                        },
                    ],
                },
                {
                    "name": "activity",
                    "fields": [
                        {
                            "name": "last_login",
                            "data_categories": ["user.behavior"],
                        },
                    ],
                },
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": [first_dataset.fides_key, second_dataset.fides_key],
            "egress": None,
            "ingress": None,
        },
    )

    return privacy_declaration


@pytest.fixture(scope="function")
def system_multiple_decs(db: Session, system: System) -> Generator[System, None, None]:
    """
    Add an additional PrivacyDeclaration onto the base System to test scenarios with
    multiple PrivacyDeclarations on a given system
    """
    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )

    db.refresh(system)
    yield system


@pytest.fixture(scope="function")
def system_third_party_sharing(db: Session) -> Generator[System, None, None]:
    system_third_party_sharing = System.create(
        db=db,
        data={
            "fides_key": f"system_third_party_sharing-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system_third_party_sharing.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )
    db.refresh(system_third_party_sharing)
    yield system_third_party_sharing
    db.delete(system_third_party_sharing)


@pytest.fixture(scope="function")
def system_provide_service(db: Session) -> System:
    system_provide_service = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "The source service, system, or product being provided to the user",
            "system_id": system_provide_service.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "essential.service",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )
    db.refresh(system_provide_service)
    return system_provide_service


@pytest.fixture(scope="function")
def system_provide_service_operations_support_optimization(db: Session) -> System:
    system_provide_service_operations_support_optimization = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Optimize and improve support operations in order to provide the service",
            "system_id": system_provide_service_operations_support_optimization.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "essential.service.operations.improve",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )
    db.refresh(system_provide_service_operations_support_optimization)
    return system_provide_service_operations_support_optimization


@pytest.fixture
def system_manager_client(db, system):
    """Return a client assigned to a system for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[],
        systems=[system.id],
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


@pytest.fixture
def connection_client(db, connection_config):
    """Return a client assigned to a connection for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[],
        systems=[],
        connections=[connection_config.id],
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


@pytest.fixture(scope="function")
def privacy_request_erasure_pending(db: Session, erasure_policy: Policy) -> Generator:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_id": erasure_policy.id,
            "status": "pending",
            "external_id": "b5d78237-f831-4add-8a88-883a4843b016",
        },
    )
    yield pr
    pr.delete(db=db)


@pytest.fixture(scope="function")
def privacy_request_requires_manual_finalization(
    db: Session, erasure_policy: Policy
) -> Generator:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_id": erasure_policy.id,
            "status": "requires_manual_finalization",
            "external_id": "b5d78237-f831-4add-8a88-883a4843b016",
        },
    )
    yield pr
    pr.delete(db=db)
