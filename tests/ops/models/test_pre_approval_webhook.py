import pytest
from sqlalchemy.orm import Session

from fides.api.db.base_class import KeyOrNameAlreadyExists, KeyValidationError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.pre_approval_webhook import (
    PreApprovalWebhook,
    PreApprovalWebhookReply,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.util.text import to_snake_case


class TestPreApprovalWebhookModel:
    def test_create_pre_approval_webhook(
        self, db: Session, https_connection_config
    ) -> None:
        name_1 = "new pre approval webhook"
        name_2 = "other pre approval webhook"
        webhook_1 = PreApprovalWebhook.create(
            db=db,
            data={
                "connection_config_id": https_connection_config.id,
                "name": name_1,
                "key": "some_service_webhook",
            },
        )

        webhook_2 = PreApprovalWebhook.create(
            db=db,
            data={
                "connection_config_id": https_connection_config.id,
                "name": name_2,
            },
        )
        assert webhook_2.key == to_snake_case(name_2)

        db.add(webhook_1)
        db.add(webhook_2)
        db.commit()

        loaded_webhook = db.query(PreApprovalWebhook).filter_by(name=name_1).first()

        assert loaded_webhook.key == "some_service_webhook"
        assert loaded_webhook.name == name_1
        assert loaded_webhook.connection_config_id == https_connection_config.id
        assert loaded_webhook.created_at is not None

        # assert relationship with ConnectionConfig
        all_webhooks_with_specific_connection_config = (
            db.query(PreApprovalWebhook)
            .filter_by(connection_config_id=https_connection_config.id)
            .all()
        )
        connection_config = (
            db.query(ConnectionConfig).filter_by(id=https_connection_config.id).first()
        )
        assert loaded_webhook.connection_config == connection_config
        assert (
            connection_config.pre_approval_webhooks
            == all_webhooks_with_specific_connection_config
        )

        connection_config.delete(db=db)
        for webhook in all_webhooks_with_specific_connection_config:
            webhook.delete(db=db)

    def test_create_connection_config_errors(
        self, db: Session, https_connection_config, pre_approval_webhooks
    ):
        with pytest.raises(KeyValidationError) as exc:
            new_webhook_no_key = PreApprovalWebhook.create(
                db=db,
                data={
                    "connection_config_id": https_connection_config.id,
                },
            )
            db.add(new_webhook_no_key)
            db.commit()
        assert str(exc.value) == "PreApprovalWebhook requires a name."

        with pytest.raises(KeyOrNameAlreadyExists) as exc:
            new_webhook_duplicate_key = PreApprovalWebhook.create(
                db=db,
                data={
                    "connection_config_id": https_connection_config.id,
                    "key": "pre_approval_webhook_2",
                },
            )
            db.add(new_webhook_duplicate_key)
            db.commit()
        assert (
            str(exc.value)
            == "Key pre_approval_webhook_2 already exists in PreApprovalWebhook. Keys will be snake-cased names if not provided. "
            "If you are seeing this error without providing a key, please provide a key or a different name."
        )

    def test_create_pre_approval_webhook_reply(
        self,
        db: Session,
        privacy_request_status_pending,
        https_connection_config,
        pre_approval_webhooks,
    ):
        reply = PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": https_connection_config.id,
                "privacy_request_id": privacy_request_status_pending.id,
                "is_eligible": True,
            },
        )
        db.add(reply)
        db.commit()

        loaded_reply = PreApprovalWebhookReply.get_by(
            db, field="privacy_request_id", value=privacy_request_status_pending.id
        )

        assert loaded_reply.webhook_id == https_connection_config.id
        assert loaded_reply.privacy_request_id == privacy_request_status_pending.id
        assert loaded_reply.is_eligible is True
        assert loaded_reply.created_at is not None

        # assert relationship with PrivacyRequest
        privacy_request = (
            db.query(PrivacyRequest)
            .filter_by(id=privacy_request_status_pending.id)
            .first()
        )
        assert loaded_reply.privacy_request == privacy_request
        assert privacy_request.pre_approval_webhook_replies[0] == loaded_reply

        reply.delete(db=db)
