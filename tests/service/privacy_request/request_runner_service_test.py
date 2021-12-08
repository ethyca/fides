import json
from typing import Any, Dict
from unittest import mock
from unittest.mock import Mock

import pydash
import pytest
from sqlalchemy import (
    column,
    table,
    select,
)
from sqlalchemy.orm import Session

from fidesops.db.session import get_db_session, get_db_engine
from fidesops.models.policy import DataCategory
from fidesops.models.privacy_request import PrivacyRequest, ExecutionLog
from fidesops.service.connectors import PostgreSQLConnector
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner
from fidesops.util.async_util import wait_for


@mock.patch("fidesops.service.privacy_request.request_runner_service.upload")
def test_policy_upload_called(
    upload_mock: Mock,
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    wait_for(privacy_request_runner.submit())
    assert upload_mock.called


def test_start_processing_sets_started_processing_at(
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    privacy_request.started_processing_at = None
    wait_for(privacy_request_runner.submit())

    _sessionmaker = get_db_session()
    db = _sessionmaker()
    privacy_request = PrivacyRequest.get(db=db, id=privacy_request.id)
    assert privacy_request.started_processing_at is not None


def test_start_processing_doesnt_overwrite_started_processing_at(
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    before = privacy_request.started_processing_at
    wait_for(privacy_request_runner.submit())
    privacy_request = PrivacyRequest.get(db=db, id=privacy_request.id)
    assert privacy_request.started_processing_at == before


def get_privacy_request_results(
    db, policy, cache, privacy_request_data: Dict[str, Any]
) -> PrivacyRequest:
    """Utility method to run a privacy request and return results after waiting for
    the returned future."""
    kwargs = {
        "requested_at": pydash.get(privacy_request_data, "requested_at"),
        "policy_id": policy.id,
        "status": "pending",
        # "client_id": client.id,
    }
    optional_fields = ["started_processing_at", "finished_processing_at"]
    for field in optional_fields:
        try:
            attr = getattr(privacy_request_data, field)
            if attr is not None:
                kwargs[field] = attr
        except AttributeError:
            pass
    privacy_request = PrivacyRequest.create(db=db, data=kwargs)

    print(json.dumps(privacy_request_data, indent=2))
    for identity in privacy_request_data["identities"]:
        privacy_request.cache_identity(identity)
        if "encryption_key" in privacy_request_data:
            privacy_request.cache_encryption(privacy_request_data["encryption_key"])

    wait_for(
        PrivacyRequestRunner(
            cache=cache,
            db=db,
            privacy_request=privacy_request,
        ).submit()
    )

    return PrivacyRequest.get(db=db, id=privacy_request.id)


@pytest.mark.integration
def test_create_and_process_access_request(
    postgres_example_test_dataset_config_read_access,
    db,
    cache,
    policy,
):

    customer_email = "customer-1@example.com"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identities": [{"email": customer_email}],
    }

    pr = get_privacy_request_results(db, policy, cache, data)

    results = pr.get_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    log_id = pr.execution_logs[0].id
    pr_id = pr.id

    policy.delete(db=db)
    pr.delete(db=db)
    db.expunge_all()
    assert ExecutionLog.get(db, id=log_id).privacy_request_id == pr_id


@pytest.mark.integration_erasure
def test_create_and_process_erasure_request_specific_category(
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
    read_connection_config,
):
    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identities": [{"email": customer_email}],
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    example_postgres_uri = PostgreSQLConnector(read_connection_config).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(engine=engine)
    integration_db = SessionLocal()
    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is `None`
            assert row[1] is None
    assert customer_found


@pytest.mark.integration_erasure
def test_create_and_process_erasure_request_generic_category(
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
    connection_config,
):
    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.provided.identifiable.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identities": [{"email": email}],
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    example_postgres_uri = PostgreSQLConnector(connection_config).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(engine=engine)
    integration_db = SessionLocal()
    stmt = select(
        column("id"),
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `email` field is `None` and that its data category
            # ("user.provided.identifiable.contact.email") has been erased by the parent
            # category ("user.provided.identifiable.contact")
            assert row[1] is None
            assert row[2] is not None
        else:
            # There are two rows other rows, and they should not have been erased
            assert row[1] in ["customer-1@example.com", "jane@example.com"]
    assert customer_found


@pytest.mark.integration_erasure
def test_create_and_process_erasure_request_with_table_joins(
    postgres_example_test_dataset_config,
    db,
    cache,
    erasure_policy,
    connection_config,
):
    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.provided.identifiable.financial").value
    target.save(db=db)

    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identities": [{"email": customer_email}],
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    example_postgres_uri = PostgreSQLConnector(connection_config).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(engine=engine)
    integration_db = SessionLocal()
    stmt = select(
        column("customer_id"),
        column("id"),
        column("ccn"),
        column("code"),
        column("name"),
    ).select_from(table("payment_card"))
    res = integration_db.execute(stmt).all()

    card_found = False
    for row in res:
        if row[0] == customer_id:
            card_found = True
            assert row[2] is None
            assert row[3] is None
            assert row[4] is None

    assert card_found is True


@pytest.mark.integration_erasure
def test_create_and_process_erasure_request_read_access(
    postgres_example_test_dataset_config_read_access,
    db,
    cache,
    erasure_policy,
    connection_config,
):
    customer_email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identities": [{"email": customer_email}],
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    errored_execution_logs = pr.execution_logs.filter_by(status="error")
    assert errored_execution_logs.count() == 9
    assert (
        errored_execution_logs[0].message
        == "No values were erased since this connection "
        "my_postgres_db_1_read_config has not been given write access"
    )
    pr.delete(db=db)

    example_postgres_uri = PostgreSQLConnector(connection_config).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(engine=engine)
    integration_db = SessionLocal()
    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is NOT `None`. We couldn't erase, because the ConnectionConfig only had
            # "read" access
            assert row[1] is not None
    assert customer_found
