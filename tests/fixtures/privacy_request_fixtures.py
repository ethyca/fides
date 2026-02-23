from datetime import datetime, timedelta, timezone
from typing import Any, Generator, Optional
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.fides_user import FidesUser
from fides.api.models.policy import ActionType, Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.duplicate_group import (
    DuplicateGroup,
    generate_rule_version,
)
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField,
    Identity,
    LabeledIdentity,
)
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings
from fides.service.privacy_request.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from tests.connectors.integration.saas.connector_runner import (
    generate_random_email,
    generate_random_phone_number,
)


@pytest.fixture(scope="function")
def privacy_requests(db: Session, policy: Policy) -> Generator:
    privacy_requests = []
    for count in range(3):
        privacy_requests.append(
            PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-{str(uuid4())}",
                    "started_processing_at": datetime.utcnow(),
                    "requested_at": datetime.utcnow() - timedelta(days=1),
                    "status": PrivacyRequestStatus.in_processing,
                    "origin": f"https://example.com/{count}/",
                    "policy_id": policy.id,
                    "client_id": policy.client_id,
                },
            )
        )
    yield privacy_requests
    for pr in privacy_requests:
        pr.delete(db)


def _create_privacy_request_for_policy(
    db: Session,
    policy: Policy,
    status: PrivacyRequestStatus = PrivacyRequestStatus.in_processing,
    email_identity: Optional[str] = "test@example.com",
    phone_identity: Optional[str] = "+12345678910",
) -> PrivacyRequest:
    data = {
        "external_id": f"ext-{str(uuid4())}",
        "requested_at": datetime(
            2018,
            12,
            31,
            hour=2,
            minute=30,
            second=23,
            microsecond=916482,
            tzinfo=timezone.utc,
        ),
        "status": status,
        "origin": "https://example.com/",
        "policy_id": policy.id,
        "client_id": policy.client_id,
    }
    if status != PrivacyRequestStatus.pending:
        data["started_processing_at"] = datetime(
            2019,
            1,
            1,
            hour=1,
            minute=45,
            second=55,
            microsecond=393185,
            tzinfo=timezone.utc,
        )
    pr = PrivacyRequest.create(
        db=db,
        data=data,
    )
    identity_kwargs = {"email": email_identity}
    pr.cache_identity(identity_kwargs)
    pr.persist_identity(
        db=db,
        identity=Identity(
            email=email_identity,
            phone_number=phone_identity,
        ),
    )
    return pr


@pytest.fixture(scope="function")
def privacy_request(
    db: Session, policy: Policy
) -> Generator[PrivacyRequest, None, None]:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_two_types(
    db: Session,
    policy: Policy,
) -> Generator[PrivacyRequest, None, None]:
    erasure_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "name": "Erasure Request Rule",
            "policy_id": policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    privacy_request = _create_privacy_request_for_policy(db, policy)

    yield privacy_request

    try:
        erasure_request_rule.delete(db)
    except ObjectDeletedError:
        pass

    try:
        privacy_request.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def soft_deleted_privacy_request(
    db: Session,
    policy: Policy,
    application_user: FidesUser,
) -> Generator[PrivacyRequest, None, None]:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    privacy_request.soft_delete(db, application_user.id)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def duplicate_privacy_request_group(
    db: Session,
    policy: Policy,
    application_user: FidesUser,
) -> Generator[DuplicateGroup, None, None]:
    config = DuplicateDetectionSettings(
        enabled=True,
        time_window_days=30,
        match_identity_fields=["email"],
    )
    rule_version = generate_rule_version(config)
    dedup_key = "duplicate@example.com"
    duplicate_group = DuplicateGroup.create(
        db=db,
        data={"rule_version": rule_version, "dedup_key": dedup_key},
    )
    yield duplicate_group


@pytest.fixture(scope="function")
def duplicate_privacy_request(
    db: Session,
    policy: Policy,
    application_user: FidesUser,
    duplicate_privacy_request_group: DuplicateGroup,
) -> Generator[PrivacyRequest, None, None]:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    privacy_request.update(
        db=db,
        data={
            "status": PrivacyRequestStatus.duplicate,
            "duplicate_request_group_id": duplicate_privacy_request_group.id,
        },
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def bulk_privacy_requests_with_various_identities(db: Session, policy: Policy) -> None:
    num_records = 2000000  # 2 million
    for i in range(num_records):
        random_email = generate_random_email()
        random_phone_number = generate_random_phone_number()
        _create_privacy_request_for_policy(
            db,
            policy,
            PrivacyRequestStatus.in_processing,
            random_email,
            random_phone_number,
        )
    yield
    for request in db.query(PrivacyRequest):
        request.delete(db)


@pytest.fixture(scope="function")
def request_task(db: Session, privacy_request) -> RequestTask:
    root_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": "complete",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__ROOT__:__ROOT__",
            "dataset_name": "__ROOT__",
            "collection_name": "__ROOT__",
            "upstream_tasks": [],
            "downstream_tasks": ["test_dataset:test_collection"],
            "all_descendant_tasks": [
                "test_dataset:test_collection",
                "__TERMINATE__:__TERMINATE__",
            ],
        },
    )
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "test_dataset:test_collection",
            "dataset_name": "test_dataset",
            "collection_name": "test_collection",
            "upstream_tasks": ["__ROOT__:__ROOT__"],
            "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
        },
    )
    end_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__TERMINATE__:__TERMINATE__",
            "dataset_name": "__TERMINATE__",
            "collection_name": "__TERMINATE__",
            "upstream_tasks": ["test_dataset:test_collection"],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )
    yield request_task

    try:
        end_task.delete(db)
    except ObjectDeletedError:
        pass
    try:
        request_task.delete(db)
    except ObjectDeletedError:
        pass
    try:
        root_task.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_request_task(db: Session, privacy_request) -> RequestTask:
    root_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.erasure,
            "status": "complete",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__ROOT__:__ROOT__",
            "dataset_name": "__ROOT__",
            "collection_name": "__ROOT__",
            "upstream_tasks": [],
            "downstream_tasks": ["test_dataset:test_collection"],
            "all_descendant_tasks": [
                "test_dataset:test_collection",
                "__TERMINATE__:__TERMINATE__",
            ],
        },
    )
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.erasure,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "test_dataset:test_collection",
            "dataset_name": "test_dataset",
            "collection_name": "test_collection",
            "upstream_tasks": ["__ROOT__:__ROOT__"],
            "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
        },
    )
    end_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.erasure,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__TERMINATE__:__TERMINATE__",
            "dataset_name": "__TERMINATE__",
            "collection_name": "__TERMINATE__",
            "upstream_tasks": ["test_dataset:test_collection"],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )
    yield request_task
    end_task.delete(db)
    request_task.delete(db)
    root_task.delete(db)


@pytest.fixture(scope="function")
def consent_request_task(db: Session, privacy_request) -> RequestTask:
    root_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.consent,
            "status": "complete",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__ROOT__:__ROOT__",
            "dataset_name": "__ROOT__",
            "collection_name": "__ROOT__",
            "upstream_tasks": [],
            "downstream_tasks": ["test_dataset:test_collection"],
            "all_descendant_tasks": [
                "test_dataset:test_collection",
                "__TERMINATE__:__TERMINATE__",
            ],
        },
    )
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.consent,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "test_dataset:test_collection",
            "dataset_name": "test_dataset",
            "collection_name": "test_collection",
            "upstream_tasks": ["__ROOT__:__ROOT__"],
            "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
        },
    )
    end_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.consent,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__TERMINATE__:__TERMINATE__",
            "dataset_name": "__TERMINATE__",
            "collection_name": "__TERMINATE__",
            "upstream_tasks": ["test_dataset:test_collection"],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )
    yield request_task
    end_task.delete(db)
    request_task.delete(db)
    root_task.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_erasure_policy(
    db: Session, erasure_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        erasure_policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_consent_policy(
    db: Session, consent_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_location(
    db: Session, policy: Policy
) -> Generator[PrivacyRequest, Any, None]:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    privacy_request.location = "US"
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_custom_fields(
    db: Session, policy: Policy, allow_custom_privacy_request_field_collection_enabled
) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 10, 1),
            "finished_processing_at": datetime(2021, 10, 3),
            "requested_at": datetime(2021, 10, 1),
            "status": PrivacyRequestStatus.complete,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    privacy_request.persist_custom_privacy_request_fields(
        db=db,
        custom_privacy_request_fields={
            "first_name": CustomPrivacyRequestField(label="First name", value="John"),
            "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
        },
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_custom_array_fields(
    db: Session, policy: Policy, allow_custom_privacy_request_field_collection_enabled
) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 10, 1),
            "finished_processing_at": datetime(2021, 10, 3),
            "requested_at": datetime(2021, 10, 1),
            "status": PrivacyRequestStatus.complete,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    privacy_request.persist_custom_privacy_request_fields(
        db=db,
        custom_privacy_request_fields={
            "device_ids": CustomPrivacyRequestField(
                label="Device Ids", value=["device_1", "device_2", "device_3"]
            ),
        },
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_email_identity(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 10, 1),
            "finished_processing_at": datetime(2021, 10, 3),
            "requested_at": datetime(2021, 10, 1),
            "status": PrivacyRequestStatus.complete,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    privacy_request.persist_identity(
        db=db,
        identity=Identity(email="customer-1@example.com"),
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_custom_identities(
    db: Session, policy: Policy
) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 10, 1),
            "finished_processing_at": datetime(2021, 10, 3),
            "requested_at": datetime(2021, 10, 1),
            "status": PrivacyRequestStatus.complete,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    privacy_request.persist_identity(
        db=db,
        identity=Identity(loyalty_id=LabeledIdentity(label="Loyalty ID", value="CH-1")),
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_requires_input(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    privacy_request.status = PrivacyRequestStatus.requires_input
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_awaiting_consent_email_send(
    db: Session, consent_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_awaiting_erasure_email_send(
    db: Session, erasure_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        erasure_policy,
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def audit_log(db: Session, privacy_request) -> PrivacyRequest:
    audit_log = AuditLog.create(
        db=db,
        data={
            "user_id": "system",
            "privacy_request_id": privacy_request.id,
            "action": AuditLogAction.approved,
            "message": "",
        },
    )
    yield audit_log
    audit_log.delete(db)


@pytest.fixture(scope="function")
def privacy_request_status_approved(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
        PrivacyRequestStatus.approved,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_status_pending(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
        PrivacyRequestStatus.pending,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_status_canceled(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
        PrivacyRequestStatus.canceled,
    )
    privacy_request.started_processing_at = None
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def succeeded_privacy_request(cache, db: Session, policy: Policy) -> PrivacyRequest:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 10, 1),
            "finished_processing_at": datetime(2021, 10, 3),
            "requested_at": datetime(2021, 10, 1),
            "status": PrivacyRequestStatus.complete,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    identity_kwargs = {"email": "email@example.com"}
    pr.cache_identity(identity_kwargs)
    pr.persist_identity(
        db=db,
        identity=Identity(**identity_kwargs),
    )
    yield pr
    pr.delete(db)


@pytest.fixture(scope="function")
def failed_privacy_request(db: Session, policy: Policy) -> PrivacyRequest:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 1, 1),
            "finished_processing_at": datetime(2021, 1, 2),
            "requested_at": datetime(2020, 12, 31),
            "status": PrivacyRequestStatus.error,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield pr
    pr.delete(db)
