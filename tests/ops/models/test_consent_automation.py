from sqlalchemy import and_
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.consent_automation import ConsentableItem, ConsentAutomation


class TestConsentAutomation:

    def test_create_consent_automation(
        self, db: Session, connection_config: ConnectionConfig
    ):
        consentable_items = [
            {
                "type": "Channel",
                "external_id": 1,
                "name": "Marketing channel (email)",
                "children": [
                    {
                        "type": "Message type",
                        "external_id": 1,
                        "name": "Weekly Ads",
                    }
                ],
            }
        ]

        ConsentAutomation.create_or_update(
            db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )
        consent_automation = ConsentAutomation.get_by(
            db, field="connection_config_id", value=connection_config.id
        )
        assert consent_automation is not None
        assert consent_automation.connection_config_id == connection_config.id
        assert len(consent_automation.consentable_items) == 2

        # test link from connection_config
        db.refresh(connection_config)
        assert len(connection_config.consent_automation.consentable_items) == 2

    def test_update_consent_automation_add_consentable_items(
        self, db: Session, connection_config, privacy_notice
    ):
        consentable_items = [
            {
                "type": "Channel",
                "external_id": 1,
                "name": "Marketing channel (email)",
                "children": [
                    {
                        "type": "Message type",
                        "external_id": 1,
                        "name": "Weekly Ads",
                    }
                ],
            }
        ]

        ConsentAutomation.create_or_update(
            db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )
        consent_automation = ConsentAutomation.get_by(
            db, field="connection_config_id", value=connection_config.id
        )
        assert consent_automation is not None
        assert consent_automation.connection_config_id == connection_config.id
        assert len(consent_automation.consentable_items) == 2
        assert consent_automation.consentable_items[0].notice_id is None
        assert consent_automation.consentable_items[1].notice_id is None

        consentable_items[0]["notice_id"] = privacy_notice.id
        consent_automation.update(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )

        consent_automation = ConsentAutomation.get_by(
            db, field="connection_config_id", value=connection_config.id
        )
        assert consent_automation is not None
        assert consent_automation.connection_config_id == connection_config.id
        assert len(consent_automation.consentable_items) == 2

        for consentable_item in consent_automation.consentable_items:
            if consentable_item.name == "Marketing channel (email)":
                assert consentable_item.notice_id == privacy_notice.id
            if consentable_item.name == "Weekly Ads":
                assert consentable_item.notice_id is None

        consent_automation.delete(db)

    def test_update_consent_automation_remove_consentable_items(
        self, db: Session, connection_config
    ):
        consentable_items = [
            {
                "type": "Channel",
                "external_id": 1,
                "name": "Marketing channel (email)",
                "children": [
                    {
                        "type": "Message type",
                        "external_id": 1,
                        "name": "Weekly Ads",
                    }
                ],
            }
        ]

        ConsentAutomation.create_or_update(
            db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )
        consent_automation = ConsentAutomation.get_by(
            db, field="connection_config_id", value=connection_config.id
        )
        assert consent_automation is not None
        assert consent_automation.connection_config_id == connection_config.id
        assert len(consent_automation.consentable_items) == 2
        assert consent_automation.consentable_items[0].notice_id is None
        assert consent_automation.consentable_items[1].notice_id is None

        consentable_items[0]["children"] = []
        consent_automation.update(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )

        consent_automation = ConsentAutomation.get_by(
            db, field="connection_config_id", value=connection_config.id
        )
        assert consent_automation is not None
        assert consent_automation.connection_config_id == connection_config.id
        assert len(consent_automation.consentable_items) == 1

        consent_automation.delete(db)

    def test_consent_automation_delete(self, db: Session, connection_config):
        """
        Verify the related consentable items are deleted when the consent automation is deleted.
        """

        consentable_items = [
            {
                "type": "Channel",
                "external_id": 1,
                "name": "Marketing channel (email)",
                "children": [
                    {
                        "type": "Message type",
                        "external_id": 1,
                        "name": "Weekly Ads",
                    }
                ],
            }
        ]

        consent_automation = ConsentAutomation.create_or_update(
            db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )

        consentable_items = (
            db.query(ConsentableItem)
            .filter(ConsentableItem.consent_automation_id == consent_automation.id)
            .all()
        )
        assert len(consentable_items) == 2

        consent_automation.delete(db)

        consentable_items = (
            db.query(ConsentableItem)
            .filter(ConsentableItem.consent_automation_id == consent_automation.id)
            .all()
        )
        assert len(consentable_items) == 0

    def test_consentable_item_delete(self, db: Session, connection_config):
        """
        Verify the child consentable items are deleted when the parent is deleted.
        """

        consentable_items = [
            {
                "type": "Channel",
                "external_id": 1,
                "name": "Marketing channel (email)",
                "children": [
                    {
                        "type": "Message type",
                        "external_id": 1,
                        "name": "Weekly Ads",
                    }
                ],
            }
        ]

        consent_automation = ConsentAutomation.create_or_update(
            db,
            data={
                "connection_config_id": connection_config.id,
                "consentable_items": consentable_items,
            },
        )

        consentable_items = (
            db.query(ConsentableItem)
            .filter(
                and_(
                    ConsentableItem.consent_automation_id == consent_automation.id,
                    ConsentableItem.parent_id.is_(None),
                )
            )
            .all()
        )
        assert len(consentable_items) == 1

        parent_consentable_item = consentable_items[0]
        parent_consentable_item.delete(db)

        consentable_items = (
            db.query(ConsentableItem)
            .filter(ConsentableItem.consent_automation_id == consent_automation.id)
            .all()
        )
        assert len(consentable_items) == 0
