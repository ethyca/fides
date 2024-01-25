import pytest
from sqlalchemy.exc import IntegrityError

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
        assert history.disabled is False
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

    def test_update_privacy_experience_config_translations_same(self, db):
        """Assert if PrivacyExperienceConfig is updated, its version is bumped and a new historical record is created"""
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


class TestPrivacyExperience:
    def test_get_experiences_by_region(self, db):
        """Test PrivacyExperience.get_experiences_by_region method"""
        (
            queried_overlay_exp,
            queried_pc_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_tx
        )
        assert queried_overlay_exp is None
        assert queried_pc_exp is None

        overlay_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        (
            queried_overlay_exp,
            queried_pc_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_tx
        )
        assert queried_overlay_exp == overlay_exp
        assert queried_pc_exp is None

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_tx",
            },
        )

        (
            queried_overlay_exp,
            queried_pc_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_tx
        )
        assert queried_overlay_exp == overlay_exp
        assert queried_pc_exp == pc_exp

        overlay_exp.delete(db)
        pc_exp.delete(db)

    def test_get_experience_by_component_and_region(self, db):
        """Test PrivacyExperience.get_experience_by_region_and_component method"""
        assert (
            PrivacyExperience.get_experience_by_region_and_component(
                db, PrivacyNoticeRegion.at, ComponentType.overlay
            )
            is None
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "at",
            },
        )

        assert (
            PrivacyExperience.get_experience_by_region_and_component(
                db, PrivacyNoticeRegion.at, ComponentType.overlay
            )
            is None
        )
        assert (
            PrivacyExperience.get_experience_by_region_and_component(
                db, PrivacyNoticeRegion.at, ComponentType.privacy_center
            )
            == pc_exp
        )

        db.delete(pc_exp)

    def test_unlink_privacy_experience_config(
        self, db, experience_config_privacy_center
    ):
        """
        Test Experience.unlink_experience_config unlinks the experience
        """
        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "at",
                "experience_config_id": experience_config_privacy_center.id,
            },
        )
        created_at = pc_exp.created_at
        updated_at = pc_exp.updated_at

        assert pc_exp.experience_config == experience_config_privacy_center
        pc_exp.unlink_experience_config(db)
        db.refresh(pc_exp)

        assert pc_exp.experience_config_id is None
        assert pc_exp.created_at == created_at
        assert pc_exp.updated_at > updated_at

        pc_exp.delete(db)

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

    def test_get_should_show_banner(self, db):
        """Test PrivacyExperience.get_should_show_banner that is calculated at runtime"""
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.privacy_center,
                "region": "it",
            },
        )

        # This is a privacy center component so whether we should show the banner is not relevant here
        assert privacy_experience.get_should_show_banner(db) is False

        privacy_experience.component = ComponentType.overlay
        privacy_experience.save(db)

        # This is an overlay component but there are no relevant notices here either
        assert privacy_experience.get_should_show_banner(db) is False

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "banner_enabled": "always_enabled",
                "component": "overlay",
                "translations": [
                    {
                        "language": "en_us",
                        "accept_button_label": "Accept all",
                        "acknowledge_button_label": "OK",
                        "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                        "privacy_preferences_link_label": "Manage preferences",
                        "privacy_policy_link_label": "View our privacy policy",
                        "privacy_policy_url": "http://example.com/privacy",
                        "reject_button_label": "Reject all",
                        "save_button_label": "Save",
                        "title": "Control your privacy",
                    }
                ],
            },
        )

        # Link experience config
        privacy_experience.experience_config_id = config.id
        privacy_experience.save(db)

        # Banner delivery required because experience config says that banner is always enabled
        assert privacy_experience.get_should_show_banner(db) is True

        config.banner_enabled = "enabled_where_required"
        config.save(db)

        # No notices
        assert privacy_experience.get_should_show_banner(db) is False

        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test privacy notice",
                "notice_key": "test_privacy_notice",
                "description": "a test sample privacy notice configuration",
                "translations": [
                    {
                        "language": "en_us",
                        "title": "Test privacy notice",
                        "description": "a test sample privacy notice configuration",
                    }
                ],
                # "regions": [PrivacyNoticeRegion.fr, PrivacyNoticeRegion.it],
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                # "displayed_in_overlay": False,
                # "displayed_in_api": True,
                # "displayed_in_privacy_center": True,
            },
        )

        config.privacy_notices.append(privacy_notice)
        config.save(db)

        # Privacy Notice linked, but its consent mechanism is opt out
        assert privacy_experience.get_should_show_banner(db) is False

        privacy_notice.consent_mechanism = ConsentMechanism.opt_in
        privacy_notice.save(db)

        # Relevant privacy notice is opt in, so it should be delivered in a banner
        assert privacy_experience.get_should_show_banner(db) is True

        # Remove notices
        privacy_notice.translations[0].delete(db)
        privacy_notice.delete(db)

    def test_get_should_show_banner_for_a_tcf_overlay(
        self, privacy_experience_france_tcf_overlay, db
    ):
        """Currently, this returns true if the experience is a TCF Overlay type"""
        assert privacy_experience_france_tcf_overlay.get_should_show_banner(db) is True

    def test_create_multiple_experiences_of_same_component_type(self, db):
        """We can only have one experience per component type per region"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        with pytest.raises(IntegrityError):
            PrivacyExperience.create(
                db=db,
                data={
                    "component": "overlay",
                    "region": "us_tx",
                },
            )

        exp.delete(db)

    def test_update_multiple_experiences_of_same_component_type(self, db):
        """We can only have one experience per component type per region. Unique constraint prevents
        Experience updates from getting in a bad state"""
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

        with pytest.raises(IntegrityError):
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
                "privacy_notices": ["test_privacy_notice"],
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

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )
        assert overlay_experience is None
        assert privacy_center_experience is None

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == [PrivacyNoticeRegion.us_ak]
        assert unlinked == []

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
        A PrivacyExperience exists for AK, but needs to be linked to this ExperienceConfig.
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

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )
        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == [PrivacyNoticeRegion.us_ak]
        assert unlinked == []

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id == config.id

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

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )

        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )
        db.refresh(privacy_center_experience)

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == []
        assert unlinked == []

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
        assert pc_exp.experience_config_id == config.id
        assert config.experiences.count() == 1

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )

        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[]  # Empty region list will remove regions
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == []
        assert unlinked == [PrivacyNoticeRegion.us_ak]
        db.refresh(config)
        assert config.experiences.count() == 0

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id is None

        privacy_center_experience.delete(db)
        for translation in config.translations:
            translation.histories[0].delete(db)
            translation.delete(db)
        config.delete(db)
