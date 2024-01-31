from copy import copy

import pytest

from fides.api.models.privacy_experience import (
    BannerEnabled,
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    PrivacyExperienceConfigHistory,
    get_privacy_notices_by_region_and_component,
    upsert_privacy_experiences_after_config_update,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    Language,
    PrivacyNotice,
    PrivacyNoticeRegion,
)


class TestExperienceConfig:
    def test_create_privacy_experience_config(self, db):
        """Assert PrivacyExperienceConfig, a translation, and its historical record are created"""
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "overlay",
                "banner_enabled": "enabled_where_required",
                "translations": [
                    {
                        "language": "en_us",
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Control Your Privacy",
                    }
                ],
            },
        )
        assert config.banner_enabled == BannerEnabled.enabled_where_required
        assert config.component == ComponentType.overlay

        translation = config.translations[0]

        assert translation.accept_button_label == "Accept all"
        assert translation.acknowledge_button_label == "OK"
        assert (
            translation.description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert (
            translation.banner_description
            == "We care about your privacy. You can accept, reject, or manage your preferences in detail."
        )
        assert translation.banner_title == "Control Your Privacy"
        assert translation.is_default is False
        assert translation.privacy_preferences_link_label == "Manage preferences"
        assert translation.privacy_policy_link_label == "View our privacy policy"
        assert translation.privacy_policy_url == "http://example.com/privacy"
        assert translation.reject_button_label == "Reject all"
        assert translation.save_button_label == "Save"
        assert translation.title == "Control your privacy"

        assert translation.histories.count() == 1

        history = translation.histories[0]
        assert translation.experience_config_history_id == history.id

        assert history.accept_button_label == "Accept all"
        assert history.acknowledge_button_label == "OK"
        assert history.banner_enabled == BannerEnabled.enabled_where_required
        assert history.component == ComponentType.overlay
        assert (
            history.description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert (
            history.banner_description
            == "We care about your privacy. You can accept, reject, or manage your preferences in detail."
        )
        assert history.banner_title == "Control Your Privacy"
        assert history.disabled is True
        assert history.is_default is False
        assert history.privacy_preferences_link_label == "Manage preferences"
        assert history.privacy_policy_link_label == "View our privacy policy"
        assert history.privacy_policy_url == "http://example.com/privacy"
        assert history.reject_button_label == "Reject all"
        assert history.save_button_label == "Save"
        assert history.title == "Control your privacy"
        assert history.version == 1.0

        history.delete(db)
        translation.delete(db)
        config.delete(db=db)

    def test_update_privacy_experience_config_level(self, db):
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "overlay",
                "banner_enabled": "enabled_where_required",
                "translations": [
                    {
                        "language": Language.en_us,
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Control Your Privacy",
                    }
                ],
            },
        )
        config_created_at = config.created_at
        config_updated_at = config.updated_at

        config.update(
            db=db,
            data={
                "component": "privacy_center",
                "translations": [
                    {
                        "language": Language.en_us,
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "banner_description": "We care about your privacy. You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Control Your Privacy",
                    }
                ],
            },
        )
        db.refresh(config)

        assert config.component == ComponentType.privacy_center
        assert config.created_at == config_created_at
        assert config.updated_at > config_updated_at

        translation = config.translations[0]
        db.refresh(translation)
        assert translation.version == 2.0
        assert translation.histories.count() == 2
        history = translation.histories.order_by(
            PrivacyExperienceConfigHistory.created_at
        )[1]
        assert history.component == ComponentType.privacy_center
        assert translation.experience_config_history_id == history.id

        old_history = translation.histories.order_by(
            PrivacyExperienceConfigHistory.created_at
        )[0]
        assert old_history.version == 1.0
        assert old_history.component == ComponentType.overlay

        translation.delete(db)
        old_history.delete(db)
        history.delete(db)

    def test_update_privacy_experience_config_add_translation(
        self, db, experience_config_overlay
    ):
        updated_at = experience_config_overlay.updated_at

        experience_config_overlay.update(
            db=db,
            data={
                "translations": [
                    {
                        "language": Language.en_us,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    },
                    {
                        "language": Language.en_gb,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    },
                ],
            },
        )
        db.refresh(experience_config_overlay)
        assert experience_config_overlay.updated_at == updated_at

        assert len(experience_config_overlay.translations) == 2
        translation = experience_config_overlay.translations[0]
        assert translation.language == Language.en_us
        assert translation.histories.count() == 1

        translation_gb = experience_config_overlay.translations[1]
        assert translation_gb.language == Language.en_gb
        assert translation_gb.histories.count() == 1

    def test_update_privacy_experience_config_update_translation(
        self, db, experience_config_overlay
    ):
        updated_at = experience_config_overlay.updated_at

        experience_config_overlay.update(
            db=db,
            data={
                "translations": [
                    {
                        "language": Language.en_us,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent!",
                    }
                ],
            },
        )
        db.refresh(experience_config_overlay)
        assert experience_config_overlay.updated_at == updated_at

        assert len(experience_config_overlay.translations) == 1
        translation = experience_config_overlay.translations[0]
        assert translation.language == Language.en_us
        assert translation.histories.count() == 2
        assert translation.title == "Manage your consent!"
        assert translation.histories.count() == 2

        assert translation.histories[0].title == "Manage your consent"
        assert translation.histories[0].version == 1.0

        assert translation.histories[1].title == "Manage your consent!"
        assert translation.histories[1].version == 2.0

    def test_update_privacy_experience_config_remove_translation(
        self, db, experience_config_overlay
    ):
        updated_at = copy(experience_config_overlay.updated_at)

        translation = experience_config_overlay.translations[0]
        history = translation.histories[0]

        experience_config_overlay.update(
            db=db,
            data={
                "component": "privacy_center",
                "translations": [],
            },
        )

        assert experience_config_overlay.updated_at != updated_at
        assert experience_config_overlay.component == ComponentType.privacy_center

        assert len(experience_config_overlay.translations) == 0

        db.refresh(history)
        assert history.version == 1.0
        assert history.translation_id is None

    def test_update_privacy_experience_config_update_notices(
        self, db, experience_config_overlay, privacy_notice
    ):
        assert experience_config_overlay.privacy_notices == []
        experience_config_overlay.save(db)

        experience_config_overlay.update(
            db=db,
            data={
                "privacy_notice_ids": [privacy_notice.id],
                "translations": [
                    {
                        "language": Language.en_us,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )
        db.refresh(experience_config_overlay)
        assert experience_config_overlay.privacy_notices == [privacy_notice]

        db.refresh(experience_config_overlay)
        assert len(experience_config_overlay.translations) == 1
        translation = experience_config_overlay.translations[0]
        assert translation.histories.count() == 1

        experience_config_overlay.update(
            db=db,
            data={
                "privacy_notice_ids": [],
                "translations": [
                    {
                        "language": Language.en_us,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )

        db.refresh(experience_config_overlay)
        assert experience_config_overlay.privacy_notices == []

    def test_update_privacy_experience_config_update_regions(
        self, db, experience_config_overlay
    ):
        assert experience_config_overlay.experiences.count() == 0
        updated_at = experience_config_overlay.updated_at
        experience_config_overlay.update(
            db=db,
            data={
                "regions": [PrivacyNoticeRegion.us_ca],
                "translations": [
                    {
                        "language": Language.en_us,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )

        db.refresh(experience_config_overlay)
        assert experience_config_overlay.regions == [PrivacyNoticeRegion.us_ca]

        exp = experience_config_overlay.experiences.first()
        exp_id = exp.id

        assert exp.experience_config_id == experience_config_overlay.id
        assert experience_config_overlay.updated_at == updated_at

        experience_config_overlay.update(
            db=db,
            data={
                "regions": [],
                "translations": [
                    {
                        "language": Language.en_us,
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                    }
                ],
            },
        )

        db.refresh(experience_config_overlay)
        assert experience_config_overlay.regions == []
        assert experience_config_overlay.experiences.count() == 0

        assert (
            db.query(PrivacyExperience).filter(PrivacyExperience.id == exp_id).first()
            is None
        )


class TestPrivacyExperience:
    def test_create_privacy_experience(self, db):
        """Assert PrivacyExperience is created as expected"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        assert exp.component == ComponentType.overlay
        assert exp.region == PrivacyNoticeRegion.us_tx
        assert exp.experience_config_id is None

        exp.delete(db=db)

    def test_update_privacy_experience(self, db, experience_config_overlay):
        """Assert PrivacyExperience is updated as expected"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_ca",
            },
        )
        exp_created_at = exp.created_at
        exp_updated_at = exp.updated_at
        assert exp.experience_config is None

        exp.update(
            db=db,
            data={
                "experience_config_id": experience_config_overlay.id,
            },
        )
        db.refresh(exp)

        assert exp.component == ComponentType.overlay
        assert exp.region == PrivacyNoticeRegion.us_ca
        assert exp.experience_config == experience_config_overlay
        assert exp.id is not None
        assert exp.created_at == exp_created_at
        assert exp.updated_at > exp_updated_at

        exp.delete(db)

    def test_create_multiple_experiences_of_same_component_type(self, db):
        """This is now allowed at the Experience level - we mostly want to check at the ExperienceConfig level
        that we don't have overlapping regions on the same *enabled* ExperienceConfig"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        exp_2 = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        exp_2.delete(db)
        exp.delete(db)

    def test_update_multiple_experiences_of_same_component_type(self, db):
        """This is allowed - we have other checks at the ExperienceConfig level to make sure there are
        no two regions attached to ExperienceConfigs of the same UX type or fides js UX type
        """
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        exp_2 = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_tx",
            },
        )

        exp_2.update(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        exp_2.delete(db)
        exp.delete(db)

    @pytest.mark.parametrize(
        "region,country",
        [
            ("us_ca", "us"),
            ("us_tx", "us"),
            ("us", "us"),
            ("ca_qc", "ca"),
            ("ca", "ca"),
            ("fr", "fr"),
        ],
    )
    def test_region_country_property(self, db, region, country):
        exp: PrivacyExperience = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": region,
            },
        )

        assert exp.region_country == country

        exp.delete(db)

    def test_get_privacy_notices_by_region_and_component(self, db):
        """
        Test that `get_privacy_notices_by_region_and_component` properly
        finds notices against multiple regions.
        """

        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test privacy notice",
                "notice_key": "test_privacy_notice",
                "description": "a test sample privacy notice configuration",
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_overlay": False,
                "displayed_in_api": True,
                "displayed_in_privacy_center": True,
            },
        )
        assert (
            get_privacy_notices_by_region_and_component(
                db,
                [PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us],
                ComponentType.privacy_center,
            ).all()
            == []
        )

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "enabled_where_required",
                "regions": [PrivacyNoticeRegion.us],
                "privacy_notice_ids": [privacy_notice.id],
                "translations": [
                    {
                        "language": Language.en_us,
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                        "privacy_policy_url": "https://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Manage your consent",
                        "description": "On this page you can opt in and out of these data uses cases",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "Confirm",
                        "banner_description": "You can accept, reject, or manage your preferences in detail.",
                        "banner_title": "Manage Your Consent",
                    }
                ],
            },
        )

        assert (
            get_privacy_notices_by_region_and_component(
                db,
                [PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us],
                ComponentType.privacy_center,
            ).all()[0]
            == privacy_notice
        )

        assert (
            get_privacy_notices_by_region_and_component(
                db,
                [PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us],
                ComponentType.overlay,
            ).all()
            == []
        )

        assert (
            get_privacy_notices_by_region_and_component(
                db, [PrivacyNoticeRegion.us], ComponentType.privacy_center
            ).all()[0]
            == privacy_notice
        )
        assert (
            get_privacy_notices_by_region_and_component(
                db,
                [PrivacyNoticeRegion.us, PrivacyNoticeRegion.fr],
                ComponentType.privacy_center,
            ).all()[0]
            == privacy_notice
        )
        assert (
            get_privacy_notices_by_region_and_component(
                db, [PrivacyNoticeRegion.us_ca], ComponentType.privacy_center
            ).all()
            == []
        )
        assert (
            get_privacy_notices_by_region_and_component(
                db,
                [PrivacyNoticeRegion.us_ca, PrivacyNoticeRegion.us_tx],
                ComponentType.privacy_center,
            ).all()
            == []
        )

        for translation in privacy_notice.translations:
            translation.histories[0].delete(db)
            translation.delete(db)


class TestUpsertPrivacyExperiencesOnConfigChange:
    def test_experience_config_created_no_matching_experience_exists(self, db):
        """Test a privacy center ExperienceConfig is created and we attempt to link AK.
        No PrivacyExperience exists yet so we create one.
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "translations": [
                    {"language": "en_us", "title": "Control your privacy"}
                ],
            },
        )

        assert (
            PrivacyExperience.get_experiences_by_region_and_component(
                db, PrivacyNoticeRegion.us_ak, ComponentType.privacy_center
            ).count()
            == 0
        )

        linked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )

        pc_exps = PrivacyExperience.get_experiences_by_region_and_component(
            db, PrivacyNoticeRegion.us_ak, ComponentType.privacy_center
        )
        assert pc_exps.count() == 1
        privacy_center_experience = pc_exps.first()

        assert privacy_center_experience is not None
        assert linked == [PrivacyNoticeRegion.us_ak]

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id == config.id

        privacy_center_experience.delete(db)
        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)

    def test_experience_config_created_matching_unlinked_experience_exists(self, db):
        """Test ExperienceConfig created and we attempt to link AK to that ExperienceConfig.
        Existing PrivacyExperiences of the same type aren't applicable here
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "translations": [
                    {"language": "en_us", "title": "Control your privacy"}
                ],
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_ak",
            },
        )
        assert pc_exp.experience_config_id is None

        linked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )

        assert config.experiences.count() == 1

        privacy_center_experience = config.experiences.first()
        assert linked == [PrivacyNoticeRegion.us_ak]

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id == config.id

        # Previously we only had one experience per region of any given type but that
        # constraint has been relaxed
        assert privacy_center_experience.id != pc_exp.id

        privacy_center_experience.delete(db)
        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)

    def test_experience_config_updated_matching_experience_already_linked(self, db):
        """Privacy Center Experience Config updated, and we attempt to add AK to this,
        but it is already linked, so no action needed"""

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "translations": [
                    {"language": "en_us", "title": "Control your privacy"}
                ],
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_ak",
                "experience_config_id": config.id,
            },
        )
        assert pc_exp.experience_config_id == config.id

        assert config.experiences.count() == 1
        assert config.experiences.first() == pc_exp

        linked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )

        assert pc_exp.experience_config_id == config.id

        assert config.experiences.count() == 1
        privacy_center_experience = config.experiences.first()
        assert privacy_center_experience == pc_exp

        db.refresh(privacy_center_experience)

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id == config.id

        privacy_center_experience.delete(db)
        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)

    def test_experience_config_unlinks_region(self, db):
        """Privacy Center Experience Config updated, and we attempt to remove the
        regions."""

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "translations": [
                    {"language": "en_us", "title": "Control your privacy"}
                ],
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_ak",
                "experience_config_id": config.id,
            },
        )
        pc_exp_id = pc_exp.id

        assert pc_exp.experience_config_id == config.id
        assert config.experiences.count() == 1

        upsert_privacy_experiences_after_config_update(
            db, config, regions=[]  # Empty region list will remove regions
        )

        assert config.experiences.count() == 0

        assert (
            db.query(PrivacyExperience)
            .filter(PrivacyExperience.id == pc_exp_id)
            .count()
            == 0
        )

        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)
