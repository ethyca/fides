from sqlalchemy.orm import Session

from fides.api.models.consent_automation import ConsentAutomation


class TestConsentAutomation:
    def test_consentable_items(self, db: Session, connection_config):
        consentable_items = [
            {
                "type": "Channel",
                "id": 1,
                "name": "Marketing channel (email)",
                "notice_id": "not_e0a4dbd1-7a66-4a5d-9ce8-f2d3125f84c8",
                "children": [
                    {
                        "type": "Message type",
                        "id": 1,
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
        assert consent_automation.consentable_items == consentable_items
