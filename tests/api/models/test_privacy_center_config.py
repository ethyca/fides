from sqlalchemy.orm import Session

from fides.api.models.privacy_center_config import (
    PrivacyCenterConfig,
    default_privacy_center_config,
)


class TestPrivacyCenterConfig:
    def test_create_or_update_keeps_single_record(self, db: Session):
        # create the record
        config_record = PrivacyCenterConfig.create_or_update(
            db=db, data={"config": default_privacy_center_config}
        )
        assert config_record.config == default_privacy_center_config
        assert len(db.query(PrivacyCenterConfig).all()) == 1

        config_record_db = db.query(PrivacyCenterConfig).first()
        assert config_record_db.config == default_privacy_center_config
        assert config_record_db.id == config_record.id

        # issue another create_or_update and verify that only the config value changes for the existing row
        # no new rows should be created
        updated_privacy_center_config = {
            "config": {
                "actions": [
                    {
                        "policy_key": "default_access_policy",
                        "title": "Access your data",
                        "identity_inputs": {"email": "required"},
                    },
                ],
            }
        }
        new_config_record = PrivacyCenterConfig.create_or_update(
            db=db, data={"config": updated_privacy_center_config}
        )
        assert len(db.query(PrivacyCenterConfig).all()) == 1

        new_config_record_db = db.query(PrivacyCenterConfig).first()
        assert new_config_record_db.config == updated_privacy_center_config
        assert new_config_record_db.id == new_config_record.id
