"""Script to create test data for the Admin UI"""

import asyncio
import string
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import orm

from fides.api.database.database import init_db
from fides.api.db.session import get_db_session
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.fides_user import FidesUser
from fides.api.models.policy import Policy, Rule, RuleTarget
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.models.storage import StorageConfig
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fides.api.util.data_category import DataCategory
from fides.config import get_config

CONFIG = get_config()


def _create_dsr_policy(
    db: orm.Session,
    action_type: str,
    client_id: str,
    policy_key: str,
) -> Policy:
    """
    Util method to create policies
    """
    policy = Policy.get_by(db=db, field="key", value=policy_key)

    if policy:
        # If the Policy is already created, don't create it again
        return policy
    else:
        policy = Policy.create(
            db=db, data={"client_id": client_id, "name": policy_key, "key": policy_key}
        )
        policy.save(db=db)

    rand = string.ascii_lowercase[:5]
    data = {}
    if action_type == ActionType.erasure.value:
        data = {
            "action_type": action_type,
            "name": f"{action_type} Rule {rand}",
            "policy_id": policy.id,
            "masking_strategy": {
                "strategy": "null_rewrite",
                "configuration": {},
            },
            "client_id": client_id,
        }
    elif action_type == ActionType.access.value:
        _, storage_config = StorageConfig.get_or_create(
            db=db,
            data={
                "name": "test storage config",
                "type": StorageType.s3,
                "details": {
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                    StorageDetails.BUCKET.value: "test_bucket",
                },
                "key": f"storage_config_for_{policy_key}",
                "format": ResponseFormat.html,
            },
        )
        data = {
            "action_type": action_type,
            "name": f"{action_type} Rule {rand}",
            "policy_id": policy.id,
            "storage_destination_id": storage_config.id,
            "client_id": client_id,
        }

    rule = Rule.create(
        db=db,
        data=data,
    )

    RuleTarget.create(
        db=db,
        data={
            "data_category": DataCategory("user.name").value,
            "rule_id": rule.id,
            "client_id": client_id,
        },
    )
    return policy


def _create_connection_configs(db: orm.Session) -> None:
    ConnectionConfig.get_or_create(
        db=db,
        data={
            "key": "ci_create_test_data_datastore_connection",
            "name": "seed datastore connection",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
        },
    )
    ConnectionConfig.get_or_create(
        db=db,
        data={
            "key": "ci_create_test_data_datastore_connection_disabled",
            "name": "seed datastore connection disabled",
            "connection_type": ConnectionType.mysql,
            "access": AccessLevel.read,
            "disabled": True,
            "disabled_at": datetime.utcnow(),
        },
    )
    ConnectionConfig.get_or_create(
        db=db,
        data={
            "key": "ci_create_test_data_saas_connection",
            "name": "seed saas connection",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
        },
    )
    ConnectionConfig.get_or_create(
        db=db,
        data={
            "key": "ci_create_test_data_saas_connection_disabled",
            "name": "seed saas connection disabled",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "disabled": True,
            "disabled_at": datetime.utcnow(),
        },
    )


def create_test_data(db: orm.Session) -> FidesUser:
    """Script to create test data for the Admin UI"""
    print("Seeding database with privacy requests")
    _, client = ClientDetail.get_or_create(
        db=db,
        data={
            "fides_key": "ci_create_test_data",
            "hashed_secret": "autoseededdata",
            "salt": "autoseededdata",
            "scopes": [],
            "roles": [],
        },
    )

    policies = []
    policies.append(
        _create_dsr_policy(
            db=db,
            action_type=ActionType.erasure.value,
            client_id=client.id,
            policy_key="delete",
        )
    )
    policies.append(
        _create_dsr_policy(
            db=db,
            action_type=ActionType.access.value,
            client_id=client.id,
            policy_key="download",
        )
    )

    for policy in policies:
        for status in PrivacyRequestStatus.__members__.values():
            pr = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-{uuid4()}",
                    "started_processing_at": datetime.utcnow(),
                    "requested_at": datetime.utcnow() - timedelta(days=1),
                    "status": status,
                    "origin": f"https://example.com/{status.value}/",
                    "policy_id": policy.id,
                    "client_id": policy.client_id,
                },
            )
            pr.persist_identity(
                db=db,
                identity=Identity(
                    email="test@example.com",
                    phone_number="+12345678910",
                ),
            )
            for action_type in [
                AuditLogAction.denied,  # Run denied before approved to simulate a realistic order
                AuditLogAction.approved,
                AuditLogAction.finished,
            ]:
                AuditLog.create(
                    db=session,
                    data={
                        "user_id": "system",
                        "privacy_request_id": pr.id,
                        "action": action_type,
                        "message": f"Audit log for request with id {pr.id} and action_type {action_type}",
                    },
                )

            for action_type in [
                ActionType.access.value,
                ActionType.erasure.value,
            ]:
                for exl_status in [
                    ExecutionLogStatus.in_processing,
                    ExecutionLogStatus.pending,
                    ExecutionLogStatus.complete,
                    ExecutionLogStatus.error,
                    ExecutionLogStatus.awaiting_processing,
                    ExecutionLogStatus.retrying,
                    ExecutionLogStatus.skipped,
                ]:
                    ExecutionLog.create(
                        db=db,
                        data={
                            "dataset_name": "dummy_dataset",
                            "collection_name": "dummy_collection",
                            "fields_affected": [
                                {
                                    "path": "dummy_dataset:dummy_collection:dummy_field_1",
                                    "field_name": "dummy_field",
                                    "data_categories": [
                                        "data_category_1",
                                        "data_category_2",
                                    ],
                                },
                                {
                                    "path": "dummy_dataset:dummy_collection:dummy_field_2",
                                    "field_name": "dummy_field_2",
                                    "data_categories": [
                                        "data_category_2",
                                        "data_category_3",
                                    ],
                                },
                            ],
                            "action_type": action_type,
                            "status": exl_status,
                            "privacy_request_id": pr.id,
                            "message": f"Execution log for request id {pr.id} status {status} and action_type {action_type}",
                        },
                    )

    print("Adding connection configs")
    _create_connection_configs(db)
    print("Data seeding complete!")


if __name__ == "__main__":
    asyncio.run(init_db(CONFIG.database.sqlalchemy_database_uri))
    session_local = get_db_session(CONFIG)
    with session_local() as session:
        create_test_data(session)
