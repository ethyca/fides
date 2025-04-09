import pytest

from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.comment import Comment, CommentReference
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.schemas.policy import ActionType


class TestManualWebhook:
    def test_manual_webhook(
        self, integration_manual_webhook_config, access_manual_webhook
    ):
        assert (
            integration_manual_webhook_config.access_manual_webhook
            == access_manual_webhook
        )
        assert (
            access_manual_webhook.connection_config == integration_manual_webhook_config
        )

    def test_get_enabled_no_enabled_webhooks(self, db):
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_enabled_webhooks(self, db, access_manual_webhook):
        assert AccessManualWebhook.get_enabled(db) == [access_manual_webhook]

    def test_get_enabled_access_webhooks(
        self, db, integration_manual_webhook_config, access_manual_webhook
    ):
        assert AccessManualWebhook.get_enabled(db, ActionType.access) == [
            access_manual_webhook
        ]

        integration_manual_webhook_config.enabled_actions = [ActionType.erasure]
        integration_manual_webhook_config.save(db)

        # don't return webhook if the access action is disabled
        assert AccessManualWebhook.get_enabled(db, ActionType.access) == []

    def test_get_enabled_erasure_webhooks(
        self, db, integration_manual_webhook_config, access_manual_webhook
    ):
        assert AccessManualWebhook.get_enabled(db, ActionType.erasure) == [
            access_manual_webhook
        ]

        integration_manual_webhook_config.enabled_actions = [ActionType.access]
        integration_manual_webhook_config.save(db)

        # don't return webhook if the erasure action is disabled
        assert AccessManualWebhook.get_enabled(db, ActionType.erasure) == []

    @pytest.mark.usefixtures("access_manual_webhook")
    def test_get_enabled_webhooks_connection_config_disabled(
        self, db, integration_manual_webhook_config
    ):
        integration_manual_webhook_config.disabled = True
        integration_manual_webhook_config.save(db)
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_enabled_webhooks_connection_config_fields_is_none(
        self, db, access_manual_webhook
    ):
        access_manual_webhook.fields = None
        access_manual_webhook.save(db)
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_enabled_webhooks_connection_config_fields_is_empty(
        self, db, access_manual_webhook
    ):
        access_manual_webhook.fields = []
        access_manual_webhook.save(db)
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_comment_by_id(self, db, access_manual_webhook, comment):
        """Test retrieving a comment associated with a manual webhook."""
        # Create a comment reference
        comment_ref = CommentReference(
            comment_id=comment.id,
            reference_id=access_manual_webhook.id,
            reference_type="manual_step",
        )
        db.add(comment_ref)
        db.commit()

        # Test getting the comment
        retrieved_comment = access_manual_webhook.get_comment_by_id(db, comment.id)
        assert retrieved_comment == comment

        # Test getting non-existent comment
        non_existent = access_manual_webhook.get_comment_by_id(db, "fake_id")
        assert non_existent is None

    def test_get_attachment_by_id(self, db, access_manual_webhook, attachment):
        """Test retrieving an attachment associated with a manual webhook."""
        # Create an attachment reference
        attachment_ref = AttachmentReference(
            attachment_id=attachment.id,
            reference_id=access_manual_webhook.id,
            reference_type="manual_step",
        )
        db.add(attachment_ref)
        db.commit()

        # Test getting the attachment
        retrieved_attachment = access_manual_webhook.get_attachment_by_id(
            db, attachment.id
        )
        assert retrieved_attachment == attachment

        # Test getting non-existent attachment
        non_existent = access_manual_webhook.get_attachment_by_id(db, "fake_id")
        assert non_existent is None

    def test_delete_attachment_by_id(self, db, access_manual_webhook, attachment):
        """Test deleting an attachment associated with a manual webhook."""
        # Create an attachment reference
        attachment_ref = AttachmentReference(
            attachment_id=attachment.id,
            reference_id=access_manual_webhook.id,
            reference_type="manual_step",
        )
        db.add(attachment_ref)
        db.commit()

        # Delete the attachment
        access_manual_webhook.delete_attachment_by_id(db, attachment.id)

        # Verify attachment is deleted
        assert access_manual_webhook.get_attachment_by_id(db, attachment.id) is None

    def test_relationships(self, db, access_manual_webhook, comment, attachment):
        """Test the relationship properties of manual webhook."""
        # Create references
        comment_ref = CommentReference(
            comment_id=comment.id,
            reference_id=access_manual_webhook.id,
            reference_type="manual_step",
        )
        attachment_ref = AttachmentReference(
            attachment_id=attachment.id,
            reference_id=access_manual_webhook.id,
            reference_type="manual_step",
        )
        db.add_all([comment_ref, attachment_ref])
        db.commit()

        # Test relationship properties
        assert comment in access_manual_webhook.comments
        assert attachment in access_manual_webhook.attachments

        # Test ordering by created_at
        assert access_manual_webhook.comments == sorted(
            access_manual_webhook.comments, key=lambda x: x.created_at
        )
        assert access_manual_webhook.attachments == sorted(
            access_manual_webhook.attachments, key=lambda x: x.created_at
        )

    def test_manual_webhook_with_multiple_types(
        self, integration_manual_webhook_config, db
    ):
        """Test creating a manual webhook with multiple types per field"""
        manual_webhook = AccessManualWebhook.create(
            db=db,
            data={
                "connection_config_id": integration_manual_webhook_config.id,
                "fields": [
                    {
                        "pii_field": "medical_records",
                        "dsr_package_label": "medical_records",
                        "data_categories": ["user.medical"],
                        "types": ["string", "file"],
                    },
                    {
                        "pii_field": "patient_notes",
                        "dsr_package_label": "patient_notes",
                        "data_categories": ["user.medical.notes"],
                        "types": ["string"],
                    },
                ],
            },
        )
        assert len(manual_webhook.fields) == 2
        assert manual_webhook.fields[0]["types"] == ["string", "file"]
        assert manual_webhook.fields[1]["types"] == ["string"]
