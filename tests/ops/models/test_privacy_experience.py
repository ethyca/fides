from fides.api.ops.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    ExperienceLanguage,
    PrivacyExperience,
)
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
)


class TestExperienceLanguage:
    def test_create_privacy_experience_language(self, db):
        """Assert ExperienceLanguage and its historical record are created
        Note that the ExperienceLanguage doesn't have regions specifically defined on it.
        """
        lang = ExperienceLanguage.create(
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

        assert lang.disabled is False
        assert lang.component == ComponentType.overlay
        assert lang.delivery_mechanism == DeliveryMechanism.banner
        assert lang.component_title == "Control your privacy"
        assert (
            lang.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert lang.banner_title == "Manage your consent"
        assert (
            lang.banner_description
            == "By clicking accept you consent to one of these methods by us and our third parties."
        )
        assert lang.link_label is None
        assert lang.confirmation_button_label == "Accept all"
        assert lang.reject_button_label == "Reject all"
        assert lang.acknowledgement_button_label is None
        assert lang.version == 1.0

        assert lang.histories.count() == 1
        history = lang.histories[0]
        assert lang.experience_language_history_id == history.id
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
        lang.delete(db=db)

    def test_update_privacy_experience_language(self, db):
        """Assert PrivacyExperienceLanguage and its historical record are created"""
        lang = ExperienceLanguage.create(
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
        lang_created_at = lang.created_at
        lang_updated_at = lang.updated_at

        lang.update(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "link_label": "Manage your privacy",
            },
        )
        db.refresh(lang)

        assert lang.disabled is False
        assert lang.component == ComponentType.privacy_center
        assert lang.delivery_mechanism == DeliveryMechanism.link
        assert lang.component_title == "Control your privacy"
        assert (
            lang.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert lang.link_label == "Manage your privacy"
        assert lang.version == 2.0

        assert lang.id is not None
        assert lang.created_at == lang_created_at
        assert lang.updated_at > lang_updated_at

        assert lang.histories.count() == 2
        history = lang.histories[1]
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.component_title == "Control your privacy"
        assert (
            history.component_description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert history.link_label == "Manage your privacy"
        assert lang.version == 2.0

        assert lang.experience_language_history_id == history.id

        old_history = lang.histories[0]
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

    def test_unlink_privacy_experience_language(
        self, db, experience_language_privacy_center
    ):
        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "region": "eu_at",
                "experience_language_id": experience_language_privacy_center.id,
                "experience_language_history_id": experience_language_privacy_center.experience_language_history_id,
            },
        )
        created_at = pc_exp.created_at
        updated_at = pc_exp.updated_at

        assert pc_exp.experience_language == experience_language_privacy_center
        pc_exp.unlink_privacy_experience_language(db)
        db.refresh(pc_exp)

        assert pc_exp.experience_language_id is None
        assert pc_exp.experience_language_history_id is None
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
        """Assert PrivacyExperience and its historical record are created"""
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

        # Privacy Notice both has a matching region,and is displayed in overlay
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
