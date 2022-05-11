from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import orm
import string

from fidesops.core.config import config
from fidesops.db.database import init_db
from fidesops.db.session import get_db_session
from fidesops.models.client import ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.policy import ActionType, Policy, Rule, RuleTarget
from fidesops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.models.storage import StorageConfig, ResponseFormat
from fidesops.schemas.storage.storage import (
    FileNaming,
    StorageDetails,
    StorageType,
)
from fidesops.util.data_category import DataCategory


"""Script to create test data for the Admin UI"""


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
            "name": policy_key,
            "key": policy_key,
            "client_id": client_id,
        },
    )

    if not created:
        # If the Policy is already created, don't create it again
        return policy

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


def create_test_data(db: orm.Session) -> FidesopsUser:
    """Script to create test data for the Admin UI"""
    print(f"Seeding database with privacy requests")
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
            PrivacyRequest.create(
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

    print(f"Data seeding complete!")


if __name__ == "__main__":
    init_db(config.database.SQLALCHEMY_DATABASE_URI)
    session_local = get_db_session()
    with session_local() as session:
        create_test_data(session)
