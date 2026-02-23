from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.policy import PolicyPostWebhook, PolicyPreWebhook
from fides.api.models.pre_approval_webhook import PreApprovalWebhook


@pytest.fixture(scope="function")
def policy_pre_execution_webhooks_oauth2(
    db: Session, https_connection_config_with_oauth, policy
) -> Generator:
    pre_webhook = PolicyPreWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config_with_oauth.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "pre_execution_one_way_webhook_oauth2",
            "order": 0,
        },
    )
    pre_webhook_two = PolicyPreWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config_with_oauth.id,
            "policy_id": policy.id,
            "direction": "two_way",
            "name": str(uuid4()),
            "key": "pre_execution_two_way_webhook_oauth2",
            "order": 1,
        },
    )
    db.commit()
    yield [pre_webhook, pre_webhook_two]
    try:
        pre_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        pre_webhook_two.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy_pre_execution_webhooks(
    db: Session, https_connection_config, policy
) -> Generator:
    pre_webhook = PolicyPreWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "pre_execution_one_way_webhook",
            "order": 0,
        },
    )
    pre_webhook_two = PolicyPreWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "two_way",
            "name": str(uuid4()),
            "key": "pre_execution_two_way_webhook",
            "order": 1,
        },
    )
    db.commit()
    yield [pre_webhook, pre_webhook_two]
    try:
        pre_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        pre_webhook_two.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy_post_execution_webhooks(
    db: Session, https_connection_config, policy
) -> Generator:
    post_webhook = PolicyPostWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "cache_busting_webhook",
            "order": 0,
        },
    )
    post_webhook_two = PolicyPostWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "cleanup_webhook",
            "order": 1,
        },
    )
    db.commit()
    yield [post_webhook, post_webhook_two]
    try:
        post_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        post_webhook_two.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def pre_approval_webhooks(
    db: Session,
    https_connection_config,
) -> Generator:
    pre_approval_webhook = PreApprovalWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "name": str(uuid4()),
            "key": "pre_approval_webhook",
        },
    )
    pre_approval_webhook_two = PreApprovalWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "name": str(uuid4()),
            "key": "pre_approval_webhook_2",
        },
    )
    db.commit()
    yield [pre_approval_webhook, pre_approval_webhook_two]
    try:
        pre_approval_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        pre_approval_webhook_two.delete(db)
    except ObjectDeletedError:
        pass
