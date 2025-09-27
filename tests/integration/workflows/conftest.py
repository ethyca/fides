from typing import Generator
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session
from fides.api.models.client import ClientDetail
from fides.api.models.policy import Policy, Rule, RuleTarget
from fides.api.models.storage import StorageConfig
from fides.api.models.policy import ActionType
from fides.api.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fides.api.util.data_category import DataCategory


@pytest.fixture(scope="function")
def local_html_storage_config(db: Session) -> StorageConfig:
    name = str(uuid4())
    data = {
        "name": name,
        "type": StorageType.local,
        "details": {
            StorageDetails.NAMING.value: FileNaming.request_id.value,
        },
        "key": "my_test_config_local",
        "format": ResponseFormat.html,
    }
    storage_config = StorageConfig.get_by_key_or_id(db, data=data)
    if storage_config is None:
        storage_config = StorageConfig.create(
            db=db,
            data=data,
        )
    return storage_config


@pytest.fixture(scope="function")
def policy(
    db: Session,
    oauth_client: ClientDetail,
    local_html_storage_config: StorageConfig,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy",
            "key": "access_policy",
            "client_id": oauth_client.id,
            "execution_timeframe": 7,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_request_policy.id,
            "storage_destination_id": local_html_storage_config.id,
        },
    )

    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": access_request_rule.id,
        },
    )
    return access_request_policy
