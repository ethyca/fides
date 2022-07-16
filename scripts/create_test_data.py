"""Script to create test data for the Admin UI"""

import string
from datetime import datetime, timedelta
from uuid import uuid4

from fideslib.db.session import get_db_session
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from sqlalchemy import orm

from fidesops.core.config import config
from fidesops.db.database import init_db
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.policy import ActionType, Policy, Rule, RuleTarget
from fidesops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.models.storage import ResponseFormat, StorageConfig
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.schemas.storage.storage import FileNaming, StorageDetails, StorageType
from fidesops.util.data_category import DataCategory


def _create_policy(
    db: orm.Session,
    action_type: str,
    client_id: str,
    policy_key: str,
) -> Policy:
    """
    Util method to create policies
    """
    created, policy = Policy.get_or_create(
        db=db,
        data={
            "key": policy_key,
        },
    )

    if not created:
        # If the Policy is already created, don't create it again
        return policy
    else:
        policy.client_id = client_id
        policy.name = policy_key
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
                "format": ResponseFormat.json,
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
            "data_category": DataCategory("user.provided.identifiable.name").value,
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
        },
    )

    policies = []
    policies.append(
        _create_policy(
            db=db,
            action_type=ActionType.erasure.value,
            client_id=client.id,
            policy_key="delete",
        )
    )
    policies.append(
        _create_policy(
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
                identity=PrivacyRequestIdentity(
                    email="test@example.com",
                    phone_number="+1 234 567 8910",
                ),
            )

    print("Adding connection configs")
    _create_connection_configs(db)
    print("Data seeding complete!")


if __name__ == "__main__":
    init_db(config.database.SQLALCHEMY_DATABASE_URI)
    session_local = get_db_session(config)
    with session_local() as session:
        create_test_data(session)
