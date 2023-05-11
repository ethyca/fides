import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.ops.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    PrivacyExperience,
    PrivacyExperienceConfig,
    upsert_privacy_experiences_after_notice_update,
)
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
)


class TestExperienceConfig:
    def test_create_privacy_experience_config(self, db):
        """Assert PrivacyExperienceConfig and its historical record are created
        Note that the PrivacyExperienceConfig doesn't have regions specifically linked to it and that's ok!
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            },
        )

        assert config.disabled is False
        assert config.component == ComponentType.overlay
        assert config.delivery_mechanism == DeliveryMechanism.banner
        assert config.component_title == "Control your privacy"
        assert (
            config.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert config.banner_title == "Manage your consent"
        assert (
            config.banner_description
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert config.link_label is None
        assert config.confirmation_button_label == "Accept all"
        assert config.reject_button_label == "Reject all"
        assert config.acknowledgement_button_label is None
        assert config.version == 1.0

        assert config.histories.count() == 1
        history = config.histories[0]
        assert config.experience_config_history_id == history.id
        assert history.component_title == "Control your privacy"
        assert (
            history.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert history.banner_title == "Manage your consent"
        assert (
            history.banner_description
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert history.link_label is None
        assert history.confirmation_button_label == "Accept all"
        assert history.reject_button_label == "Reject all"
        assert history.acknowledgement_button_label is None
        assert history.version == 1.0

        history.delete(db)
        config.delete(db=db)

    def test_update_privacy_experience_config(self, db):
        """Assert if PrivacyExperienceConfig is updated, its version is bumped and a new historical record is created"""
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            },
        )
        lang_created_at = config.created_at
        lang_updated_at = config.updated_at

        config.update(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "link_label": "Manage your privacy",
            },
        )
        db.refresh(config)

        assert config.disabled is False
        assert config.component == ComponentType.privacy_center
        assert config.delivery_mechanism == DeliveryMechanism.link
        assert config.component_title == "Control your privacy"
        assert (
            config.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert config.link_label == "Manage your privacy"
        assert config.version == 2.0

        assert config.id is not None
        assert config.created_at == lang_created_at
        assert config.updated_at > lang_updated_at

        assert config.histories.count() == 2
        history = config.histories[1]
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.component_title == "Control your privacy"
        assert (
            history.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert history.link_label == "Manage your privacy"
        assert config.version == 2.0

        assert config.experience_config_history_id == history.id

        old_history = config.histories[0]
        assert old_history.version == 1.0
        assert old_history.component == ComponentType.overlay
        assert old_history.delivery_mechanism == DeliveryMechanism.banner

        old_history.delete(db)
        history.delete(db)


class TestPrivacyExperience:
    def test_get_experiences_by_region(self, db):
        (
            queried_overlay_exp,
            queried_pc_exp,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_tx)
        assert queried_overlay_exp is None
        assert queried_pc_exp is None

        overlay_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "region": "us_tx",
            },
        )

        (
            queried_overlay_exp,
            queried_pc_exp,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_tx)
        assert queried_overlay_exp == overlay_exp
        assert queried_pc_exp is None

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "region": "us_tx",
            },
        )

        (
            queried_overlay_exp,
            queried_pc_exp,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_tx)
        assert queried_overlay_exp == overlay_exp
        assert queried_pc_exp == pc_exp

        db.delete(pc_exp.histories[0])
        db.delete(overlay_exp.histories[0])
        overlay_exp.delete(db)
        pc_exp.delete(db)

    def test_get_experience_by_component_and_region(self, db):
        assert (
            PrivacyExperience.get_experience_by_component_and_region(
                db, PrivacyNoticeRegion.eu_at, ComponentType.overlay
            )
            is None
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "region": "eu_at",
            },
        )

        assert (
            PrivacyExperience.get_experience_by_component_and_region(
                db, PrivacyNoticeRegion.eu_at, ComponentType.overlay
            )
            is None
        )
        assert (
            PrivacyExperience.get_experience_by_component_and_region(
                db, PrivacyNoticeRegion.eu_at, ComponentType.privacy_center
            )
            == pc_exp
        )

        db.delete(pc_exp.histories[0])
        db.delete(pc_exp)

    def test_unlink_privacy_experience_config(
        self, db, experience_config_privacy_center
    ):
        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "region": "eu_at",
                "experience_config_id": experience_config_privacy_center.id,
                "experience_config_history_id": experience_config_privacy_center.experience_config_history_id,
            },
        )
        created_at = pc_exp.created_at
        updated_at = pc_exp.updated_at

        assert pc_exp.experience_config == experience_config_privacy_center
        pc_exp.unlink_privacy_experience_config(db)
        db.refresh(pc_exp)

        assert pc_exp.experience_config_id is None
        assert pc_exp.experience_config_history_id is None
        assert pc_exp.version == 2.0
        assert pc_exp.created_at == created_at
        assert pc_exp.updated_at > updated_at

        for history in pc_exp.histories:
            history.delete(db)
        pc_exp.delete(db)

    def test_create_privacy_experience(self, db):
        """Assert PrivacyExperience and its historical record are created"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "region": "us_tx",
            },
        )

        assert exp.disabled is False
        assert exp.component == ComponentType.overlay
        assert exp.delivery_mechanism == DeliveryMechanism.banner
        assert exp.version == 1.0

        assert exp.histories.count() == 1
        history = exp.histories[0]
        assert exp.privacy_experience_history_id == history.id
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.region == PrivacyNoticeRegion.us_tx
        assert history.version == 1.0

        history.delete(db)
        exp.delete(db=db)

    def test_update_privacy_experience(self, db):
        """Assert if PrivacyExperience is updated, its version is bumped and another historical record is created"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "region": "us_ca",
            },
        )
        exp_created_at = exp.created_at
        exp_updated_at = exp.updated_at

        exp.update(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "region": "us_ut",
            },
        )
        db.refresh(exp)

        assert exp.disabled is False
        assert exp.component == ComponentType.privacy_center
        assert exp.delivery_mechanism == DeliveryMechanism.link
        assert exp.region == PrivacyNoticeRegion.us_ut

        assert exp.version == 2.0

        assert exp.id is not None
        assert exp.created_at == exp_created_at
        assert exp.updated_at > exp_updated_at

        assert exp.histories.count() == 2
        history = exp.histories[1]
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.region == PrivacyNoticeRegion.us_ut
        assert history.version == 2.0

        assert exp.privacy_experience_history_id == history.id

        old_history = exp.histories[0]
        assert old_history.version == 1.0
        assert old_history.component == ComponentType.overlay
        assert old_history.delivery_mechanism == DeliveryMechanism.banner
        assert old_history.region == PrivacyNoticeRegion.us_ca

        old_history.delete(db)
        history.delete(db)
        exp.delete(db)

    def test_get_related_privacy_notices(self, db):
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.link,
                "region": "eu_it",
            },
        )

        # No privacy notices exist
        assert privacy_experience.get_related_privacy_notices(db) == []

        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test privacy notice",
                "description": "a test sample privacy notice configuration",
                "regions": [PrivacyNoticeRegion.eu_fr, PrivacyNoticeRegion.eu_it],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_overlay": False,
                "displayed_in_api": True,
                "displayed_in_privacy_center": True,
            },
        )

        # Privacy Notice has a matching region, but is not displayed in overlay
        assert privacy_experience.get_related_privacy_notices(db) == []

        privacy_notice.displayed_in_overlay = True
        privacy_notice.save(db)

        # Privacy Notice both has a matching region and is displayed in overlay
        assert privacy_experience.get_related_privacy_notices(db) == [privacy_notice]

        privacy_notice.regions = ["us_ca"]
        privacy_notice.save(db)
        # While privacy notice is displayed in the overlay, it doesn't have a matching region
        assert privacy_experience.get_related_privacy_notices(db) == []

        privacy_notice.regions = ["eu_it"]
        privacy_notice.save(db)
        privacy_notice.disabled = True
        privacy_notice.save(db)

        assert privacy_experience.get_related_privacy_notices(db) == [privacy_notice]
        # Disabled show by default but if show_disable is False, they're removed.
        assert (
            privacy_experience.get_related_privacy_notices(db, show_disabled=False)
            == []
        )

    def test_create_multiple_experiences_of_same_component_type(self, db):
        """We can only have one experience per component type per region"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "region": "us_tx",
            },
        )

        with pytest.raises(IntegrityError):
            PrivacyExperience.create(
                db=db,
                data={
                    "component": "overlay",
                    "delivery_mechanism": "link",
                    "region": "us_tx",
                },
            )

        exp.histories[0].delete(db)
        exp.delete(db)

    def test_update_multiple_experiences_of_same_component_type(self, db):
        """We can only have one experience per component type per region. Unique constraint prevents
        Experience updates from getting in a bad state"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "region": "us_tx",
            },
        )

        exp_2 = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "region": "us_tx",
            },
        )

        with pytest.raises(IntegrityError):
            exp_2.update(
                db=db,
                data={
                    "component": "overlay",
                    "delivery_mechanism": "link",
                    "region": "us_tx",
                },
            )

        exp_2.histories[0].delete(db)
        exp_2.delete(db)
        exp.histories[0].delete(db)
        exp.delete(db)


class TestUpsertPrivacyExperiencesOnNoticeChange:
    def test_privacy_center_experience_needed(self, db):
        """
        Notice that needs to be displayed in the PrivacyCenter is created and no Privacy Center Experience
        exists.  Assert that both a privacy center PrivacyExperience and a historical record are created.
        """
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "regions": [
                    PrivacyNoticeRegion.us_ca,
                ],
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": True,
                "displayed_in_overlay": False,
                "displayed_in_api": False,
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is None
        assert privacy_center_experience is None

        added_exp, updated_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert added_exp == [privacy_center_experience]
        assert updated_exp == []

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.delivery_mechanism == DeliveryMechanism.link
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.experience_config_history_id is None
        assert privacy_center_experience.histories.count() == 1

        history = privacy_center_experience.histories[0]
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.region == PrivacyNoticeRegion.us_ca
        assert history.disabled is False
        assert history.version == 1.0
        assert history.experience_config_id is None
        assert history.experience_config_history_id is None

        assert privacy_center_experience.get_related_privacy_notices(db) == [notice]

        history.delete(db)
        privacy_center_experience.delete(db)

        notice.histories[0].delete(db)
        notice.delete(db)

    def test_privacy_center_experience_already_exists(self, db):
        """
        Notice that needs to be displayed in the PrivacyCenter is created and Privacy Center Experience
        already exists.  No action needed.
        """
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "regions": [
                    PrivacyNoticeRegion.us_ca,
                ],
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": True,
                "displayed_in_overlay": False,
                "displayed_in_api": False,
            },
        )

        exp = PrivacyExperience.create(
            db=db,
            data={
                "region": PrivacyNoticeRegion.us_ca,
                "component": ComponentType.privacy_center,
                "delivery_mechanism": DeliveryMechanism.link,
            },
        )
        exp_created_at = exp.created_at
        exp_updated_at = exp.updated_at

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is None
        assert privacy_center_experience is not None

        added_exp, updated_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert added_exp == []
        assert updated_exp == []

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.delivery_mechanism == DeliveryMechanism.link
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.experience_config_history_id is None
        assert privacy_center_experience.histories.count() == 1
        assert privacy_center_experience.created_at == exp_created_at
        assert privacy_center_experience.updated_at == exp_updated_at

        history = privacy_center_experience.histories[0]
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.region == PrivacyNoticeRegion.us_ca
        assert history.disabled is False
        assert history.version == 1.0
        assert history.experience_config_id is None
        assert history.experience_config_history_id is None

        assert privacy_center_experience.get_related_privacy_notices(db) == [notice]

        history.delete(db)
        privacy_center_experience.delete(db)

        notice.histories[0].delete(db)
        notice.delete(db)

    def test_overlay_experience_needed(self, db):
        """Test Notice created that needs to be displayed in an overlay but none exists. Assert one is created"""
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "regions": [
                    PrivacyNoticeRegion.eu_it,
                ],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["advertising"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": False,
                "displayed_in_overlay": True,
                "displayed_in_api": False,
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.eu_it)
        assert overlay_experience is None
        assert privacy_center_experience is None

        added_exp, updated_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.eu_it]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.eu_it)
        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == [overlay_experience]
        assert updated_exp == []

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.delivery_mechanism == DeliveryMechanism.banner
        assert overlay_experience.region == PrivacyNoticeRegion.eu_it
        assert overlay_experience.disabled is False
        assert overlay_experience.version == 1.0
        assert overlay_experience.experience_config_id is None
        assert overlay_experience.experience_config_history_id is None
        assert overlay_experience.histories.count() == 1

        history = overlay_experience.histories[0]
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.region == PrivacyNoticeRegion.eu_it
        assert history.disabled is False
        assert history.version == 1.0
        assert history.experience_config_id is None
        assert history.experience_config_history_id is None

        assert overlay_experience.get_related_privacy_notices(db) == [notice]

        history.delete(db)
        overlay_experience.delete(db)

        notice.histories[0].delete(db)
        notice.delete(db)

    def test_overlay_experience_exists(self, db):
        """
        Test Notice created that needs to be displayed in an overlay and experience already exists. No action needed.
        """
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "regions": [
                    PrivacyNoticeRegion.us_ca,
                ],
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["advertising"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": False,
                "displayed_in_overlay": True,
                "displayed_in_api": False,
            },
        )

        exp = PrivacyExperience.create(
            db=db,
            data={
                "region": PrivacyNoticeRegion.us_ca,
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.link,
            },
        )
        exp_created_at = exp.created_at
        exp_updated_at = exp.updated_at

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is not None
        assert privacy_center_experience is None

        added_exp, updated_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == []
        assert updated_exp == []

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.delivery_mechanism == DeliveryMechanism.link
        assert overlay_experience.region == PrivacyNoticeRegion.us_ca
        assert overlay_experience.disabled is False
        assert overlay_experience.version == 1.0
        assert overlay_experience.experience_config_id is None
        assert overlay_experience.experience_config_history_id is None
        assert overlay_experience.histories.count() == 1
        assert overlay_experience.created_at == exp_created_at
        assert overlay_experience.updated_at == exp_updated_at

        history = overlay_experience.histories[0]
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.region == PrivacyNoticeRegion.us_ca
        assert history.disabled is False
        assert history.version == 1.0
        assert history.experience_config_id is None
        assert history.experience_config_history_id is None

        assert overlay_experience.get_related_privacy_notices(db) == [notice]

        history.delete(db)
        overlay_experience.delete(db)

        notice.histories[0].delete(db)
        notice.delete(db)

    def test_link_needs_to_be_converted_to_banner(self, db):
        """
        Test Notice created that needs to be displayed in an overlay banner but an overlay link PrivacyExperience
        exists.  We need to convert that existing Experience to be displayed with a banner.

        The existing ExperienceConfig also needs to be unlinked as it's no longer valid
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "link",
                "component_title": "Control your privacy",
                "component_description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "banner_title": "Manage your consent",
                "banner_description": "By clicking accept you consent to one of these methods by us and our third parties.",
                "confirmation_button_label": "Accept all",
                "reject_button_label": "Reject all",
            },
        )

        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "regions": [
                    PrivacyNoticeRegion.eu_it,
                ],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["advertising"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": False,
                "displayed_in_overlay": True,
                "displayed_in_api": False,
            },
        )

        exp = PrivacyExperience.create(
            db=db,
            data={
                "region": PrivacyNoticeRegion.eu_it,
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.link,
                "experience_config_id": config.id,
                "experience_config_history_id": config.histories[0].id,
            },
        )
        exp_created_at = exp.created_at
        exp_updated_at = exp.updated_at

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.eu_it)
        assert overlay_experience is not None
        assert privacy_center_experience is None

        added_exp, updated_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.eu_it]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.eu_it)
        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == []
        assert updated_exp == [overlay_experience]

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.delivery_mechanism == DeliveryMechanism.banner
        assert overlay_experience.region == PrivacyNoticeRegion.eu_it
        assert overlay_experience.disabled is False
        assert overlay_experience.version == 2.0
        assert overlay_experience.experience_config_id is None
        assert overlay_experience.experience_config_history_id is None
        assert overlay_experience.histories.count() == 2
        assert overlay_experience.created_at == exp_created_at
        assert overlay_experience.updated_at > exp_updated_at

        history = overlay_experience.histories[1]
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.region == PrivacyNoticeRegion.eu_it
        assert history.disabled is False
        assert history.version == 2.0
        assert history.experience_config_id is None
        assert history.experience_config_history_id is None

        assert overlay_experience.get_related_privacy_notices(db) == [notice]

        db.refresh(config)
        assert config.version == 1.0  # Config itself wasn't updated
        assert config.histories.count() == 1

        overlay_experience.histories[0].delete(db)
        history.delete(db)
        overlay_experience.delete(db)

        notice.histories[0].delete(db)
        notice.delete(db)

        config.histories[0].delete(db)
        config.delete(db)

    def test_both_privacy_center_and_overlay_experience_needed(self, db):
        """Assert multiple types of experiences can be created simultaneously"""
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "regions": [
                    PrivacyNoticeRegion.us_ca,
                ],
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": True,
                "displayed_in_overlay": True,
                "displayed_in_api": False,
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is None
        assert privacy_center_experience is None

        added_exp, updated_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        assert overlay_experience is not None
        assert privacy_center_experience is not None
        assert {exp.id for exp in added_exp} == {
            overlay_experience.id,
            privacy_center_experience.id,
        }
        assert updated_exp == []

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.delivery_mechanism == DeliveryMechanism.link
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.experience_config_history_id is None
        assert privacy_center_experience.histories.count() == 1

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.delivery_mechanism == DeliveryMechanism.banner
        assert overlay_experience.region == PrivacyNoticeRegion.us_ca
        assert overlay_experience.disabled is False
        assert overlay_experience.version == 1.0
        assert overlay_experience.experience_config_id is None
        assert overlay_experience.experience_config_history_id is None
        assert overlay_experience.histories.count() == 1

        assert privacy_center_experience.get_related_privacy_notices(db) == [notice]
        assert overlay_experience.get_related_privacy_notices(db) == [notice]

        overlay_experience.histories[0].delete(db)
        overlay_experience.delete(db)

        privacy_center_experience.histories[0].delete(db)
        privacy_center_experience.delete(db)

        notice.histories[0].delete(db)
        notice.delete(db)
