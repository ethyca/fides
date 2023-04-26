from fides.api.ops.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    PrivacyExperience,
)
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
)


class TestPrivacyExperience:
    def test_create_privacy_experience(self, db):
        """Assert PrivacyExperience and its historical record are created"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "delivery_mechanism": "banner",
                "regions": ["us_va"],
                "component_title": "Manage your privacy",
                "banner_title": "Consent Options",
                "banner_description": "Here's where you change your consent",
                "confirmation_button_label": "Approve",
                "reject_button_label": "Discard",
            },
            check_name=False,
        )

        assert exp.disabled is False
        assert exp.component == ComponentType.overlay
        assert exp.delivery_mechanism == DeliveryMechanism.banner
        assert exp.regions == [PrivacyNoticeRegion.us_va]
        assert exp.component_title == "Manage your privacy"
        assert exp.component_description is None
        assert exp.banner_title == "Consent Options"
        assert exp.banner_description == "Here's where you change your consent"
        assert exp.link_label is None
        assert exp.confirmation_button_label == "Approve"
        assert exp.reject_button_label == "Discard"
        assert exp.acknowledgement_button_label is None
        assert exp.version == 1.0
        assert exp.privacy_experience_template_id is None

        history = exp.histories[0]
        assert exp.privacy_experience_history_id == history.id
        assert history.disabled is False
        assert history.component == ComponentType.overlay
        assert history.delivery_mechanism == DeliveryMechanism.banner
        assert history.regions == [PrivacyNoticeRegion.us_va]
        assert history.component_title == "Manage your privacy"
        assert history.component_description is None
        assert history.banner_title == "Consent Options"
        assert history.banner_description == "Here's where you change your consent"
        assert history.link_label is None
        assert history.confirmation_button_label == "Approve"
        assert history.reject_button_label == "Discard"
        assert history.acknowledgement_button_label is None
        assert history.version == 1.0
        assert history.privacy_experience_template_id is None
        assert history.privacy_experience_id == exp.id

        history.delete(db)
        exp.delete(db=db)

    def test_update_privacy_experience(self, db):
        """Assert PrivacyExperience and its historical record are created"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "delivery_mechanism": "link",
                "regions": ["eu_hu"],
                "component_title": "Manage your privacy",
                "link_label": "Go to the privacy center",
            },
            check_name=False,
        )

        assert exp.disabled is False
        assert exp.component == ComponentType.privacy_center
        assert exp.delivery_mechanism == DeliveryMechanism.link
        assert exp.regions == [PrivacyNoticeRegion.eu_hu]
        assert exp.component_title == "Manage your privacy"
        assert exp.component_description is None
        assert exp.banner_description is None
        assert exp.link_label == "Go to the privacy center"
        assert exp.version == 1.0
        assert exp.privacy_experience_template_id is None
        assert exp.acknowledgement_button_label is None

        assert exp.id is not None
        exp_created_at = exp.created_at
        exp_updated_at = exp.updated_at

        history = exp.histories[0]
        assert exp.privacy_experience_history_id == history.id
        assert history.disabled is False
        assert history.component == ComponentType.privacy_center
        assert history.delivery_mechanism == DeliveryMechanism.link
        assert history.regions == [PrivacyNoticeRegion.eu_hu]
        assert history.component_title == "Manage your privacy"
        assert history.component_description is None
        assert history.banner_description is None
        assert history.link_label == "Go to the privacy center"
        assert history.version == 1.0
        assert history.privacy_experience_template_id is None

        exp.update(
            db,
            data={
                "regions": [PrivacyNoticeRegion.eu_hu, PrivacyNoticeRegion.eu_at],
                "banner_description": "Please verify your consent_options",
            },
        )
        db.refresh(exp)
        assert exp.regions == [PrivacyNoticeRegion.eu_hu, PrivacyNoticeRegion.eu_at]
        assert exp.banner_description == "Please verify your consent_options"
        assert exp.version == 2.0
        assert exp.histories.count() == 2
        assert exp.created_at == exp_created_at
        assert exp.updated_at > exp_updated_at

        assert exp.privacy_experience_history_id == exp.histories[1].id
        history_2 = exp.histories[1]
        assert history_2.disabled is False
        assert history_2.component == ComponentType.privacy_center
        assert history_2.delivery_mechanism == DeliveryMechanism.link
        assert history_2.regions == [
            PrivacyNoticeRegion.eu_hu,
            PrivacyNoticeRegion.eu_at,
        ]
        assert history_2.component_title == "Manage your privacy"
        assert history_2.component_description is None
        assert history_2.banner_description == "Please verify your consent_options"
        assert history_2.link_label == "Go to the privacy center"
        assert history_2.version == 2.0
        assert history_2.privacy_experience_template_id is None

        history_2.delete(db)
        history.delete(db)
        exp.delete(db=db)

    def test_get_related_privacy_notices(self, db):
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.overlay,
                "delivery_mechanism": DeliveryMechanism.link,
                "regions": [PrivacyNoticeRegion.eu_fr, PrivacyNoticeRegion.eu_at],
                "component_title": "Manage your consent preferences",
                "component_description": "On this page you can opt in and out of these data uses cases",
                "link_label": "Manage your privacy",
            },
        )

        # No privacy notices exist
        assert privacy_experience.get_related_privacy_notices(db) == []

        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test privacy notice",
                "description": "a test sample privacy notice configuration",
                "regions": [PrivacyNoticeRegion.eu_fr],
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

        privacy_notice.regions = ["eu_at"]
        privacy_notice.save(db)

        # Sanity check
        assert privacy_experience.get_related_privacy_notices(db) == [privacy_notice]

        # France filter returns no notices
        assert (
            privacy_experience.get_related_privacy_notices(
                db, region=PrivacyNoticeRegion.eu_fr
            )
            == []
        )

        # Austria filter returns the one notice
        assert privacy_experience.get_related_privacy_notices(
            db, region=PrivacyNoticeRegion.eu_at
        ) == [privacy_notice]

        privacy_notice.disabled = True
        privacy_notice.save(db)

        assert privacy_experience.get_related_privacy_notices(db) == [privacy_notice]
        # Disabled show by default but if show_disable is False, they're removed.
        assert (
            privacy_experience.get_related_privacy_notices(db, show_disabled=False)
            == []
        )
