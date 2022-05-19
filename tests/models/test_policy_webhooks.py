from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.common_exceptions import WebhookOrderException
from fidesops.models.policy import PolicyPostWebhook


def test_reorder_webhooks(db: Session, policy, https_connection_config):
    for i in range(0, 5):
        PolicyPostWebhook.create(
            db=db,
            data={
                "connection_config_id": https_connection_config.id,
                "policy_id": policy.id,
                "direction": "one_way",
                "name": str(uuid4()),
                "key": f"webhook_{i}",
                "order": i,
            },
        )

    db.commit()

    webhook_four = PolicyPostWebhook.get_by(db=db, field="key", value="webhook_4")
    # Move the last webhook to the first position
    webhook_four.reorder_related_webhooks(db=db, new_index=0)

    webhooks = [
        webhook
        for webhook in policy.post_execution_webhooks.order_by(PolicyPostWebhook.order)
    ]
    assert webhooks[0].order == 0
    assert webhooks[0].key == "webhook_4"
    assert webhooks[1].order == 1
    assert webhooks[1].key == "webhook_0"
    assert webhooks[2].order == 2
    assert webhooks[2].key == "webhook_1"
    assert webhooks[3].order == 3
    assert webhooks[3].key == "webhook_2"
    assert webhooks[4].order == 4
    assert webhooks[4].key == "webhook_3"

    # Move the last webhook to the same position it's currently sitting at - no change
    webhook_four.reorder_related_webhooks(db=db, new_index=0)

    webhooks = [
        webhook
        for webhook in policy.post_execution_webhooks.order_by(PolicyPostWebhook.order)
    ]
    assert webhooks[0].order == 0
    assert webhooks[0].key == "webhook_4"
    assert webhooks[1].order == 1
    assert webhooks[1].key == "webhook_0"
    assert webhooks[2].order == 2
    assert webhooks[2].key == "webhook_1"
    assert webhooks[3].order == 3
    assert webhooks[3].key == "webhook_2"
    assert webhooks[4].order == 4
    assert webhooks[4].key == "webhook_3"

    # Move the first webhook to an invalid position
    with pytest.raises(WebhookOrderException):
        webhook_four.reorder_related_webhooks(db=db, new_index=5)

    # Move the first webhook to a negative position
    with pytest.raises(WebhookOrderException):
        webhook_four.reorder_related_webhooks(db=db, new_index=-1)

    db.refresh(webhook_four)

    # Move the first webhook to index 2
    webhook_four.reorder_related_webhooks(db=db, new_index=2)
    webhooks = [
        webhook
        for webhook in policy.post_execution_webhooks.order_by(PolicyPostWebhook.order)
    ]
    assert webhooks[0].order == 0
    assert webhooks[0].key == "webhook_0"
    assert webhooks[1].order == 1
    assert webhooks[1].key == "webhook_1"
    assert webhooks[2].order == 2
    assert webhooks[2].key == "webhook_4"
    assert webhooks[3].order == 3
    assert webhooks[3].key == "webhook_2"
    assert webhooks[4].order == 4
    assert webhooks[4].key == "webhook_3"

    policy.post_execution_webhooks.delete()
