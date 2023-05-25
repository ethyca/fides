import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.api.deps import get_api_session
from fides.api.models.privacy_experience import (
    BannerEnabled,
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    upsert_privacy_experiences_after_config_update,
    upsert_privacy_experiences_after_notice_update,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
    UserConsentPreference,
)


class TestExperienceConfig:
    def test_create_privacy_experience_config(self, db):
        """Assert PrivacyExperienceConfig and its historical record are created
        Note that the PrivacyExperienceConfig doesn't have regions specifically linked to it here.
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "accept_button_label": "Accept all",
                "acknowledge_button_label": "OK",
                "banner_enabled": "enabled_where_required",
                "component": "overlay",
                "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "privacy_preferences_link_label": "Manage preferences",
                "privacy_policy_link_label": "View our privacy policy",
                "privacy_policy_url": "example.com/privacy",
                "reject_button_label": "Reject all",
                "save_button_label": "Save",
                "title": "Control your privacy",
            },
        )

        assert config.accept_button_label == "Accept all"
        assert config.acknowledge_button_label == "OK"
        assert config.banner_enabled == BannerEnabled.enabled_where_required
        assert config.component == ComponentType.overlay
        assert (
            config.description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert config.disabled is False
        assert config.is_default is False
        assert config.privacy_preferences_link_label == "Manage preferences"
        assert config.privacy_policy_link_label == "View our privacy policy"
        assert config.privacy_policy_url == "example.com/privacy"
        assert config.reject_button_label == "Reject all"
        assert config.save_button_label == "Save"
        assert config.title == "Control your privacy"

        assert config.version == 1.0
        assert config.histories.count() == 1
        assert config.experiences.count() == 0
        assert config.regions == []

        history = config.histories[0]
        assert config.experience_config_history_id == history.id

        assert history.accept_button_label == "Accept all"
        assert history.acknowledge_button_label == "OK"
        assert history.banner_enabled == BannerEnabled.enabled_where_required
        assert history.component == ComponentType.overlay
        assert (
            history.description
            == "We care about your privacy. Opt in and opt out of the data use cases below."
        )
        assert history.disabled is False
        assert history.is_default is False
        assert history.privacy_preferences_link_label == "Manage preferences"
        assert history.privacy_policy_link_label == "View our privacy policy"
        assert history.privacy_policy_url == "example.com/privacy"
        assert history.reject_button_label == "Reject all"
        assert history.save_button_label == "Save"
        assert history.title == "Control your privacy"
        assert history.version == 1.0

        history.delete(db)
        config.delete(db=db)

    def test_update_privacy_experience_config(self, db):
        """Assert if PrivacyExperienceConfig is updated, its version is bumped and a new historical record is created"""
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "accept_button_label": "Accept all",
                "acknowledge_button_label": "OK",
                "banner_enabled": "enabled_where_required",
                "component": "overlay",
                "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "privacy_preferences_link_label": "Manage preferences",
                "privacy_policy_link_label": "View our privacy policy",
                "privacy_policy_url": "example.com/privacy",
                "reject_button_label": "Reject all",
                "save_button_label": "Save",
                "title": "Control your privacy",
            },
        )
        config_created_at = config.created_at
        config_updated_at = config.updated_at

        config.update(
            db=db,
            data={
                "component": "privacy_center",
            },
        )
        db.refresh(config)

        assert config.component == ComponentType.privacy_center
        assert config.version == 2.0
        assert config.id is not None
        assert config.created_at == config_created_at
        assert config.updated_at > config_updated_at

        assert config.histories.count() == 2
        history = config.histories[1]
        assert history.component == ComponentType.privacy_center
        assert config.experience_config_history_id == history.id

        old_history = config.histories[0]
        assert old_history.version == 1.0
        assert old_history.component == ComponentType.overlay

        old_history.delete(db)
        history.delete(db)


class TestPrivacyExperience:
    def test_get_experiences_by_region(self, db):
        """Test PrivacyExperience.get_experiences_by_region method"""
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
        """Test PrivacyExperience.get_experience_by_region_and_component method"""
        assert (
            PrivacyExperience.get_experience_by_region_and_component(
                db, PrivacyNoticeRegion.eu_at, ComponentType.overlay
            )
            is None
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "eu_at",
            },
        )

        assert (
            PrivacyExperience.get_experience_by_region_and_component(
                db, PrivacyNoticeRegion.eu_at, ComponentType.overlay
            )
            is None
        )
        assert (
            PrivacyExperience.get_experience_by_region_and_component(
                db, PrivacyNoticeRegion.eu_at, ComponentType.privacy_center
            )
            == pc_exp
        )

        db.delete(pc_exp.histories[0])
        db.delete(pc_exp)

    def test_unlink_privacy_experience_config(
        self, db, experience_config_privacy_center
    ):
        """
        Test Experience.unlink_experience_config unlinks the experience and bumps the version
        """
        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "eu_at",
                "experience_config_id": experience_config_privacy_center.id,
                "experience_config_history_id": experience_config_privacy_center.experience_config_history_id,
            },
        )
        created_at = pc_exp.created_at
        updated_at = pc_exp.updated_at

        assert pc_exp.version == 1.0
        assert pc_exp.experience_config == experience_config_privacy_center
        pc_exp.unlink_experience_config(db)
        db.refresh(pc_exp)

        assert pc_exp.experience_config_id is None
        assert pc_exp.experience_config_history_id is None
        assert pc_exp.version == 2.0
        assert pc_exp.created_at == created_at
        assert pc_exp.updated_at > updated_at

        for history in pc_exp.histories:
            history.delete(db)
        pc_exp.delete(db)

    def test_unlink_privacy_experience_config_nothing_to_unlink(self, db):
        """
        Test Experience.unlink_experience_config does nothing if no experience config is attached
        """
        pc_exp = PrivacyExperience.create(
            db=db,
            data={"component": "privacy_center", "region": "eu_at"},
        )
        created_at = pc_exp.created_at
        updated_at = pc_exp.updated_at

        assert pc_exp.version == 1.0
        assert pc_exp.experience_config is None
        pc_exp.unlink_experience_config(db)
        db.refresh(pc_exp)

        assert pc_exp.experience_config_id is None
        assert pc_exp.experience_config_history_id is None
        assert pc_exp.version == 1.0
        assert pc_exp.created_at == created_at
        assert pc_exp.updated_at == updated_at

        for history in pc_exp.histories:
            history.delete(db)
        pc_exp.delete(db)

    def test_create_privacy_experience(self, db):
        """Assert PrivacyExperience and its historical record are created"""
        exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "overlay",
                "region": "us_tx",
            },
        )

        assert exp.disabled is False
        assert exp.component == ComponentType.overlay
        assert exp.region == PrivacyNoticeRegion.us_tx
        assert exp.version == 1.0
        assert exp.experience_config_id is None
        assert exp.experience_config_history_id is None

        assert exp.histories.count() == 1
        history = exp.histories[0]
        assert exp.privacy_experience_history_id == history.id
        assert history.component == ComponentType.overlay
        assert history.region == PrivacyNoticeRegion.us_tx
        assert history.version == 1.0
        assert history.experience_config_id is None
        assert history.experience_config_history_id is None

        history.delete(db)
        exp.delete(db=db)

    def test_update_privacy_experience(self, db, experience_config_overlay):
        """Assert if PrivacyExperience is updated, its version is bumped and another historical record is created"""
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
                "experience_config_history_id": experience_config_overlay.histories[
                    0
                ].id,
            },
        )
        db.refresh(exp)

        assert exp.disabled is False
        assert exp.component == ComponentType.overlay
        assert exp.region == PrivacyNoticeRegion.us_ca
        assert exp.version == 2.0
        assert exp.experience_config == experience_config_overlay
        assert exp.id is not None
        assert exp.created_at == exp_created_at
        assert exp.updated_at > exp_updated_at

        assert exp.histories.count() == 2
        history = exp.histories[1]
        assert history.component == ComponentType.overlay
        assert history.experience_config_id == experience_config_overlay.id
        assert (
            history.experience_config_history_id
            == experience_config_overlay.histories[0].id
        )
        assert history.version == 2.0

        assert exp.privacy_experience_history_id == history.id

        old_history = exp.histories[0]
        assert old_history.version == 1.0
        assert old_history.component == ComponentType.overlay
        assert old_history.experience_config_id is None
        assert old_history.experience_config_history_id is None

        old_history.delete(db)
        history.delete(db)
        exp.delete(db)

    def test_get_related_privacy_notices(self, db):
        """Test PrivacyExperience.get_related_privacy_notices that are embedded in PrivacyExperience request"""
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.overlay,
                "region": "eu_it",
            },
        )

        # No privacy notices exist
        assert privacy_experience.get_related_privacy_notices(db) == []

        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test privacy notice",
                "notice_key": "test_privacy_notice",
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
        # Disabled show by default but if show_disable is False, they're unlinked.
        assert (
            privacy_experience.get_related_privacy_notices(db, show_disabled=False)
            == []
        )

    @pytest.mark.usefixtures("privacy_preference_history_us_ca_provide")
    def test_get_related_notices_no_privacy_preference_for_fides_user_device_id(
        self,
        db,
        privacy_notice_us_ca_provide,
        fides_user_provided_identity,
    ):
        """Test fides_user_provided_identity argument for get_related_privacy_notices when the
        user does not have saved preferences.

        By default, we still return the notices, we just don't surface current or outdated preferences for the
        user because none exist.
        """
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.overlay,
                "region": "us_ca",
            },
        )

        notices = privacy_experience.get_related_privacy_notices(db)
        assert notices == [privacy_notice_us_ca_provide]
        # No preference here, because no user passed in.
        assert notices[0].default_preference == UserConsentPreference.opt_out
        assert notices[0].current_preference is None
        assert notices[0].outdated_preference is None

        notices = privacy_experience.get_related_privacy_notices(
            db, fides_user_provided_identity=fides_user_provided_identity
        )
        assert notices == [privacy_notice_us_ca_provide]
        # User has no preferences saved for this notice
        assert notices[0].default_preference == UserConsentPreference.opt_out
        assert notices[0].current_preference is None
        assert notices[0].outdated_preference is None

    def test_get_related_privacy_notices_with_fides_user_device_id_preferences(
        self,
        db,
        privacy_notice_us_ca_provide,
        privacy_preference_history_us_ca_provide_for_fides_user,
        fides_user_provided_identity,
    ):
        """Test fides user device id argument to Experience.get_related_privacy_notices adds the user's
        preferences if they exist.  If the user's preferences correspond to an older version, that
        will go under "outdated" preference.
        """
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.overlay,
                "region": "us_ca",
            },
        )

        notices = privacy_experience.get_related_privacy_notices(db)
        assert notices == [privacy_notice_us_ca_provide]
        # No preference here, because no user passed in.
        assert notices[0].current_preference is None
        assert notices[0].outdated_preference is None

        current_saved_preference = (
            privacy_preference_history_us_ca_provide_for_fides_user.current_privacy_preference
        )
        assert current_saved_preference.preference == UserConsentPreference.opt_in

        # Current preference returned for given user
        notices = privacy_experience.get_related_privacy_notices(
            db, fides_user_provided_identity=fides_user_provided_identity
        )
        assert notices == [privacy_notice_us_ca_provide]
        assert notices[0].default_preference == UserConsentPreference.opt_out
        assert notices[0].current_preference == UserConsentPreference.opt_in
        assert notices[0].outdated_preference is None

        # Update privacy notice
        privacy_notice_us_ca_provide.update(
            db=db,
            data={
                "data_uses": ["improve"],
                "enforcement_level": EnforcementLevel.frontend,
            },
        )

        # Current preference for the given user is now None, and opt in preference is the "outdated" preference because it
        # corresponds to a preference for an older version
        refreshed_notices = privacy_experience.get_related_privacy_notices(
            db, fides_user_provided_identity=fides_user_provided_identity
        )

        assert refreshed_notices == [privacy_notice_us_ca_provide]
        assert refreshed_notices[0].default_preference == UserConsentPreference.opt_out
        assert refreshed_notices[0].current_preference is None
        assert refreshed_notices[0].outdated_preference == UserConsentPreference.opt_in

        privacy_experience.histories[0].delete(db)
        privacy_experience.delete(db)

        another_session = get_api_session()
        requeried = privacy_experience.get_related_privacy_notices(another_session)
        # Assert current/outdated preferences are None when requeried in another session w/ no device id
        assert requeried[0].default_preference == UserConsentPreference.opt_out
        assert requeried[0].current_preference is None
        assert requeried[0].outdated_preference is None
        another_session.close()

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

        exp.histories[0].delete(db)
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
                "notice_key": "example_privacy_notice",
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

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)

        assert overlay_experience is None  # Only privacy center experience was created
        assert privacy_center_experience is not None
        assert added_exp == [privacy_center_experience]

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.experience_config_history_id is None
        assert privacy_center_experience.histories.count() == 1

        history = privacy_center_experience.histories[0]
        assert history.component == ComponentType.privacy_center
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
                "notice_key": "example_privacy_notice",
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

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert added_exp == []

        assert privacy_center_experience.component == ComponentType.privacy_center
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
                "notice_key": "example_privacy_notice",
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

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.eu_it]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.eu_it)

        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == [overlay_experience]

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.region == PrivacyNoticeRegion.eu_it
        assert overlay_experience.disabled is False
        assert overlay_experience.version == 1.0
        assert overlay_experience.experience_config_id is None
        assert overlay_experience.experience_config_history_id is None
        assert overlay_experience.histories.count() == 1

        history = overlay_experience.histories[0]
        assert history.component == ComponentType.overlay
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
        Test Notice created that needs to be displayed in an overlay and experience already exists.
        No action needed.
        """
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "notice_key": "example_privacy_notice",
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

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ca)
        db.refresh(overlay_experience)

        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == []

        assert overlay_experience.component == ComponentType.overlay
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

    def test_both_privacy_center_and_overlay_experience_needed(self, db):
        """Assert multiple types of experiences can be created simultaneously"""
        notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "example privacy notice",
                "notice_key": "example_privacy_notice",
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

        added_exp = upsert_privacy_experiences_after_notice_update(
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

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.experience_config_history_id is None
        assert privacy_center_experience.histories.count() == 1

        assert overlay_experience.component == ComponentType.overlay
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


class TestUpsertPrivacyExperiencesOnConfigChange:
    def test_experience_config_created_no_matching_experience_exists(self, db):
        """Test a privacy center ExperienceConfig is created and we attempt to link AK.
        No PrivacyExperience exists yet so we create one - we do this regardless of whether notices exist.
        It's okay to have an experience without notices.
        """
        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "title": "Control your privacy",
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)
        assert overlay_experience is None
        assert privacy_center_experience is None

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == [PrivacyNoticeRegion.us_ak]
        assert unlinked == []

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.experience_config_id == config.id
        assert (
            privacy_center_experience.experience_config_history_id
            == config.histories[0].id
        )

        privacy_center_experience.histories[0].delete(db)
        privacy_center_experience.delete(db)
        config.histories[0].delete(db)
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
                "title": "Control your privacy",
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
        assert pc_exp.experience_config_history_id is None

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)
        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == [PrivacyNoticeRegion.us_ak]
        assert unlinked == []

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.version == 2.0
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.experience_config_id == config.id
        assert (
            privacy_center_experience.experience_config_history_id
            == config.histories[0].id
        )

        privacy_center_experience.histories[1].delete(db)
        privacy_center_experience.histories[0].delete(db)
        privacy_center_experience.delete(db)
        config.histories[0].delete(db)
        config.delete(db)

    def test_experience_config_updated_matching_experience_already_linked(self, db):
        """Privacy Center Experience Config updated, and we attempt to add AK to this,
        but it is already linked, so no action needed"""

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "title": "Control your privacy",
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_ak",
                "experience_config_id": config.id,
                "experience_config_history_id": config.histories[0].id,
            },
        )
        assert pc_exp.experience_config_id == config.id
        assert pc_exp.experience_config_history_id == config.histories[0].id

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)

        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[PrivacyNoticeRegion.us_ak]
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)
        db.refresh(privacy_center_experience)

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == []
        assert unlinked == []

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.version == 1.0
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.experience_config_id == config.id
        assert (
            privacy_center_experience.experience_config_history_id
            == config.histories[0].id
        )

        privacy_center_experience.histories[0].delete(db)
        privacy_center_experience.delete(db)
        config.histories[0].delete(db)
        config.delete(db)

    def test_experience_config_unlinks_region(self, db):
        """Privacy Center Experience Config updated, and we attempt to add AK to this,
        but it is already linked, so no action needed"""

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "component": "privacy_center",
                "banner_enabled": "always_disabled",
                "title": "Control your privacy",
            },
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_ak",
                "experience_config_id": config.id,
                "experience_config_history_id": config.histories[0].id,
            },
        )
        assert pc_exp.experience_config_id == config.id
        assert pc_exp.experience_config_history_id == config.histories[0].id
        assert config.experiences.count() == 1

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)

        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db, config, regions=[]  # Empty region list will remove regions
        )
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, PrivacyNoticeRegion.us_ak)

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert linked == []
        assert unlinked == [PrivacyNoticeRegion.us_ak]
        db.refresh(config)
        assert config.experiences.count() == 0

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.version == 2.0
        assert privacy_center_experience.disabled is False
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.experience_config_history_id is None

        privacy_center_experience.histories[1].delete(db)
        privacy_center_experience.histories[0].delete(db)
        privacy_center_experience.delete(db)
        config.histories[0].delete(db)
        config.delete(db)
