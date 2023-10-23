import pytest
from fideslang.gvl import MAPPED_PURPOSES, MAPPED_SPECIAL_PURPOSES
from sqlalchemy.exc import IntegrityError

from fides.api.api.deps import get_api_session
from fides.api.models.privacy_experience import (
    BannerEnabled,
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    PrivacyExperienceConfigHistory,
    cache_saved_and_served_on_consent_record,
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
from fides.api.models.privacy_preference import ConsentRecordType
from fides.api.schemas.tcf import (
    TCFFeatureRecord,
    TCFPurposeConsentRecord,
    TCFPurposeLegitimateInterestsRecord,
    TCFSpecialPurposeRecord,
    TCFVendorConsentRecord,
    TCFVendorLegitimateInterestsRecord,
    TCFVendorRelationships,
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
                "privacy_policy_url": "http://example.com/privacy",
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
        assert config.privacy_policy_url == "http://example.com/privacy"
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
        assert history.privacy_policy_url == "http://example.com/privacy"
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
                "privacy_policy_url": "http://example.com/privacy",
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
        history = config.histories.order_by(PrivacyExperienceConfigHistory.created_at)[
            1
        ]
        assert history.component == ComponentType.privacy_center
        assert config.experience_config_history_id == history.id

        old_history = config.histories.order_by(
            PrivacyExperienceConfigHistory.created_at
        )[0]
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

    def test_link_default_experience_config(self, db, experience_config_privacy_center):
        """
        Test Experience.link_default_experience_config points the experience towards the default config
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
        pc_exp.link_default_experience_config(db)
        db.refresh(pc_exp)

        assert pc_exp.experience_config_id is not None
        assert pc_exp.experience_config_id == "pri-097a-d00d-40b6-a08f-f8e50def-pri"
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

    def test_get_related_privacy_notices(self, db, system):
        """Test PrivacyExperience.get_related_privacy_notices that are embedded in PrivacyExperience request"""
        privacy_experience = PrivacyExperience.create(
            db=db,
            data={
                "component": ComponentType.overlay,
                "region": "it",
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
                "regions": [PrivacyNoticeRegion.fr, PrivacyNoticeRegion.it],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
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

        privacy_notice.regions = ["it"]
        privacy_notice.save(db)
        privacy_notice.disabled = True
        privacy_notice.save(db)

        assert privacy_experience.get_related_privacy_notices(db) == [privacy_notice]
        # Disabled show by default but if show_disable is False, they're unlinked.
        assert (
            privacy_experience.get_related_privacy_notices(db, show_disabled=False)
            == []
        )

        # Privacy notice is applicable to a system - they share a data use
        assert privacy_experience.get_related_privacy_notices(
            db, systems_applicable=True
        ) == [privacy_notice]

        system.privacy_declarations[0].delete(db)
        db.refresh(system)

        # Privacy notice is no longer applicable to any systems
        assert (
            privacy_experience.get_related_privacy_notices(db, systems_applicable=True)
            == []
        )

        privacy_notice.histories[0].delete(db)
        privacy_notice.delete(db)

    def test_get_related_privacy_notices_for_a_tcf_overlay(
        self, db, privacy_experience_france_tcf_overlay
    ):
        """Just returns an empty list; Privacy Notices are not relevant here"""
        assert (
            privacy_experience_france_tcf_overlay.get_related_privacy_notices(db) == []
        )

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

        privacy_notice = PrivacyNotice.create(
            db=db,
            data={
                "name": "Test privacy notice",
                "notice_key": "test_privacy_notice",
                "description": "a test sample privacy notice configuration",
                "regions": [PrivacyNoticeRegion.fr, PrivacyNoticeRegion.it],
                "consent_mechanism": ConsentMechanism.opt_out,
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_overlay": False,
                "displayed_in_api": True,
                "displayed_in_privacy_center": True,
            },
        )

        # Privacy Notice has a matching region, but is not displayed in overlay, so it's
        # not relevant here
        assert privacy_experience.get_should_show_banner(db) is False

        privacy_notice.displayed_in_overlay = True
        privacy_notice.save(db)

        # Privacy Notice both has a matching region and is displayed in overlay and is opt_out, so not required
        assert privacy_experience.get_should_show_banner(db) is False

        privacy_notice.consent_mechanism = ConsentMechanism.opt_in
        privacy_notice.save(db)

        # Relevant privacy notice is opt in, so it should be delivered in a banner
        assert privacy_experience.get_should_show_banner(db) is True

        config = PrivacyExperienceConfig.create(
            db=db,
            data={
                "accept_button_label": "Accept all",
                "acknowledge_button_label": "OK",
                "banner_enabled": "always_enabled",
                "component": "overlay",
                "description": "We care about your privacy. Opt in and opt out of the data use cases below.",
                "privacy_preferences_link_label": "Manage preferences",
                "privacy_policy_link_label": "View our privacy policy",
                "privacy_policy_url": "http://example.com/privacy",
                "reject_button_label": "Reject all",
                "save_button_label": "Save",
                "title": "Control your privacy",
            },
        )

        # Link experience config
        privacy_experience.experience_config_id = config.id
        privacy_experience.save(db)

        # Remove notices
        privacy_notice.histories[0].delete(db)
        privacy_notice.delete(db)

        # Banner delivery required because experience config says that banner is always enabled
        assert privacy_experience.get_should_show_banner(db) is True

        config.banner_enabled = BannerEnabled.always_disabled
        config.save(db)

        # Banner delivery not required because config says that banner should be always disabled
        assert privacy_experience.get_should_show_banner(db) is False

    def test_get_should_show_banner_for_a_tcf_overlay(
        self, privacy_experience_france_tcf_overlay, db
    ):
        """Currently, this returns true if the experience is a TCF Overlay type"""
        assert privacy_experience_france_tcf_overlay.get_should_show_banner(db) is True

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
                "data_uses": ["functional"],
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


class TestUpsertPrivacyExperiencesOnNoticeChange:
    def test_privacy_center_experience_needed(self, db):
        """
        Notice that needs to be displayed in the PrivacyCenter is created and no Privacy Center Experience
        exists.  Assert that a privacy center PrivacyExperience is created.
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
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": True,
                "displayed_in_overlay": False,
                "displayed_in_api": False,
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )
        assert overlay_experience is None
        assert privacy_center_experience is None

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )

        assert overlay_experience is None  # Only privacy center experience was created
        assert privacy_center_experience is not None
        assert added_exp == [privacy_center_experience]

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        # Experience automatically linked to default privacy center config
        assert (
            privacy_center_experience.experience_config_id
            == "pri-097a-d00d-40b6-a08f-f8e50def-pri"
        )
        assert privacy_center_experience.get_related_privacy_notices(db) == [notice]

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
                "data_uses": ["marketing.advertising", "third_party_sharing"],
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
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )
        assert overlay_experience is None
        assert privacy_center_experience is not None

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )

        assert overlay_experience is None
        assert privacy_center_experience is not None
        assert added_exp == []

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert privacy_center_experience.experience_config_id is None
        assert privacy_center_experience.created_at == exp_created_at
        assert privacy_center_experience.updated_at == exp_updated_at

        assert privacy_center_experience.get_related_privacy_notices(db) == [notice]

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
                    PrivacyNoticeRegion.it,
                ],
                "consent_mechanism": ConsentMechanism.opt_in,
                "data_uses": ["marketing.advertising"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": False,
                "displayed_in_overlay": True,
                "displayed_in_api": False,
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.it
        )
        assert overlay_experience is None
        assert privacy_center_experience is None

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.it]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.it
        )

        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == [overlay_experience]

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.region == PrivacyNoticeRegion.it
        assert (
            overlay_experience.experience_config_id
            == "pri-7ae3-f06b-4096-970f-0bbbdef-over"
        )

        assert overlay_experience.get_related_privacy_notices(db) == [notice]

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
                "data_uses": ["marketing.advertising"],
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
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )

        assert overlay_experience is not None
        assert privacy_center_experience is None

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )
        db.refresh(overlay_experience)

        assert overlay_experience is not None
        assert privacy_center_experience is None
        assert added_exp == []

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.region == PrivacyNoticeRegion.us_ca
        assert overlay_experience.experience_config_id is None
        assert overlay_experience.created_at == exp_created_at
        assert overlay_experience.updated_at == exp_updated_at

        assert overlay_experience.get_related_privacy_notices(db) == [notice]

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
                "data_uses": ["marketing.advertising", "third_party_sharing"],
                "enforcement_level": EnforcementLevel.system_wide,
                "displayed_in_privacy_center": True,
                "displayed_in_overlay": True,
                "displayed_in_api": False,
            },
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )
        assert overlay_experience is None
        assert privacy_center_experience is None

        added_exp = upsert_privacy_experiences_after_notice_update(
            db, [PrivacyNoticeRegion.us_ca]
        )

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ca
        )

        assert overlay_experience is not None
        assert privacy_center_experience is not None
        assert {exp.id for exp in added_exp} == {
            overlay_experience.id,
            privacy_center_experience.id,
        }

        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ca
        assert (
            privacy_center_experience.experience_config_id
            == "pri-097a-d00d-40b6-a08f-f8e50def-pri"
        )

        assert overlay_experience.component == ComponentType.overlay
        assert overlay_experience.region == PrivacyNoticeRegion.us_ca
        assert (
            overlay_experience.experience_config_id
            == "pri-7ae3-f06b-4096-970f-0bbbdef-over"
        )

        assert privacy_center_experience.get_related_privacy_notices(db) == [notice]
        assert overlay_experience.get_related_privacy_notices(db) == [notice]

        overlay_experience.delete(db)
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
        config.histories[0].delete(db)
        config.delete(db)

    def test_experience_config_unlinks_region(self, db):
        """Privacy Center Experience Config updated, and we attempt to remove the
        regions. Any affected experiences have the default linked instead"""

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
        assert (
            privacy_center_experience.experience_config_id
            == "pri-097a-d00d-40b6-a08f-f8e50def-pri"
        )

        privacy_center_experience.delete(db)
        config.histories[0].delete(db)
        config.delete(db)

    def test_experience_config_unlinks_region_from_default_config(self, db):
        """Default Privacy Center Experience Config updated, and we attempt to remove the
        regions. Affected experiences have no config because there's nothing to which we can automatically link.
        """
        default_privacy_center_config = PrivacyExperienceConfig.get_default_config(
            db, ComponentType.privacy_center
        )

        pc_exp = PrivacyExperience.create(
            db=db,
            data={
                "component": "privacy_center",
                "region": "us_ak",
                "experience_config_id": default_privacy_center_config.id,
            },
        )
        assert pc_exp.experience_config_id == default_privacy_center_config.id
        assert default_privacy_center_config.experiences.count() == 1

        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )

        assert overlay_experience is None
        assert privacy_center_experience == pc_exp

        linked, unlinked = upsert_privacy_experiences_after_config_update(
            db,
            default_privacy_center_config,
            regions=[],  # Empty region list will remove regions
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
        db.refresh(default_privacy_center_config)
        assert default_privacy_center_config.experiences.count() == 0

        assert privacy_center_experience.region == PrivacyNoticeRegion.us_ak
        assert privacy_center_experience.component == ComponentType.privacy_center
        assert privacy_center_experience.experience_config_id is None

        privacy_center_experience.delete(db)


class TestCacheSavedAndServedOnConsentRecord:
    @pytest.fixture
    def tcf_purpose_consent_record(self):
        return TCFPurposeConsentRecord(**MAPPED_PURPOSES[8].dict())

    @pytest.fixture
    def tcf_purpose_legitimate_interests_record(self):
        return TCFPurposeLegitimateInterestsRecord(**MAPPED_PURPOSES[8].dict())

    @pytest.mark.usefixtures(
        "served_notice_history_us_provide_for_fides_user",
        "privacy_preference_history_us_ca_provide_for_fides_user",
    )
    def test_cache_saved_and_served_for_privacy_notice_history(
        self,
        db,
        fides_user_provided_identity,
        privacy_notice_us_ca_provide,
    ):
        assert (
            privacy_notice_us_ca_provide.default_preference
            == UserConsentPreference.opt_out
        )
        assert privacy_notice_us_ca_provide.current_preference is None
        assert privacy_notice_us_ca_provide.outdated_preference is None
        assert privacy_notice_us_ca_provide.current_served is None
        assert privacy_notice_us_ca_provide.outdated_served is None

        cache_saved_and_served_on_consent_record(
            db=db,
            consent_record=privacy_notice_us_ca_provide,
            fides_user_provided_identity=fides_user_provided_identity,
            record_type=ConsentRecordType.privacy_notice_id,
        )

        assert (
            privacy_notice_us_ca_provide.default_preference
            == UserConsentPreference.opt_out
        )
        assert (
            privacy_notice_us_ca_provide.current_preference
            == UserConsentPreference.opt_in
        )
        assert privacy_notice_us_ca_provide.outdated_preference is None
        assert privacy_notice_us_ca_provide.current_served is True
        assert privacy_notice_us_ca_provide.outdated_served is None

    def test_record_for_tcf_purpose_exists_for_older_version(
        self,
        db,
        tcf_purpose_consent_record,
        fides_user_provided_identity,
        privacy_preference_history_for_tcf_purpose_consent,
        served_notice_history_for_tcf_purpose,
    ):
        privacy_preference_history_for_tcf_purpose_consent.current_privacy_preference.tcf_version = (
            "1.0"
        )
        privacy_preference_history_for_tcf_purpose_consent.current_privacy_preference.save(
            db
        )

        served_notice_history_for_tcf_purpose.last_served_record.tcf_version = "1.0"
        served_notice_history_for_tcf_purpose.last_served_record.save(db)

        cache_saved_and_served_on_consent_record(
            db,
            tcf_purpose_consent_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.purpose_consent,
        )

        assert (
            tcf_purpose_consent_record.default_preference
            == UserConsentPreference.opt_out
        )
        assert tcf_purpose_consent_record.current_preference is None
        assert (
            tcf_purpose_consent_record.outdated_preference
            == UserConsentPreference.opt_out
        )
        assert tcf_purpose_consent_record.current_served is None
        assert tcf_purpose_consent_record.outdated_served is True

    @pytest.mark.usefixtures(
        "privacy_preference_history_for_tcf_purpose_consent",
        "served_notice_history_for_tcf_purpose",
    )
    def test_record_for_tcf_purpose_exists_for_current_version(
        self, db, tcf_purpose_consent_record, fides_user_provided_identity
    ):
        cache_saved_and_served_on_consent_record(
            db,
            tcf_purpose_consent_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.purpose_consent,
        )

        assert (
            tcf_purpose_consent_record.default_preference
            == UserConsentPreference.opt_out
        )
        assert (
            tcf_purpose_consent_record.current_preference
            == UserConsentPreference.opt_out
        )
        assert tcf_purpose_consent_record.outdated_preference is None
        assert tcf_purpose_consent_record.current_served is True
        assert tcf_purpose_consent_record.outdated_served is None

    def test_no_record_for_tcf_purpose_exists(
        self, db, tcf_purpose_consent_record, fides_user_provided_identity
    ):
        cache_saved_and_served_on_consent_record(
            db,
            tcf_purpose_consent_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.purpose_consent,
        )
        assert (
            tcf_purpose_consent_record.default_preference
            == UserConsentPreference.opt_out
        )
        assert tcf_purpose_consent_record.current_preference is None
        assert tcf_purpose_consent_record.outdated_preference is None
        assert tcf_purpose_consent_record.current_served is None
        assert tcf_purpose_consent_record.outdated_served is None

    def test_tcf_purpose_legitimate_interests_record(
        self,
        db,
        tcf_purpose_legitimate_interests_record,
        fides_user_provided_identity,
        privacy_preference_history_for_tcf_purpose_legitimate_interests,
    ):
        cache_saved_and_served_on_consent_record(
            db,
            tcf_purpose_legitimate_interests_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.purpose_legitimate_interests,
        )
        assert (
            tcf_purpose_legitimate_interests_record.default_preference
            == UserConsentPreference.opt_in
        )
        assert (
            tcf_purpose_legitimate_interests_record.current_preference
            == UserConsentPreference.opt_in
        )
        assert tcf_purpose_legitimate_interests_record.outdated_preference is None
        assert tcf_purpose_legitimate_interests_record.current_served is None
        assert tcf_purpose_legitimate_interests_record.outdated_served is None

    @pytest.mark.usefixtures(
        "privacy_preference_history_for_tcf_special_purpose",
        "served_notice_history_for_tcf_special_purpose",
    )
    def test_cache_saved_and_served_for_special_purpose(
        self,
        db,
        fides_user_provided_identity,
    ):
        special_purpose_record = TCFPurposeConsentRecord(
            **MAPPED_SPECIAL_PURPOSES[1].dict()
        )
        cache_saved_and_served_on_consent_record(
            db,
            special_purpose_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.special_purpose,
        )

        assert (
            special_purpose_record.default_preference == UserConsentPreference.opt_out
        )
        assert special_purpose_record.current_preference == UserConsentPreference.opt_in
        assert special_purpose_record.outdated_preference is None
        assert special_purpose_record.current_served is True
        assert special_purpose_record.outdated_served is None

    @pytest.mark.usefixtures("privacy_preference_history_for_vendor")
    def test_cache_saved_and_served_for_vendor_consent(
        self, db, fides_user_provided_identity
    ):
        vendor_record = TCFVendorConsentRecord(
            id="gvl.42", name="test", description="test", has_vendor_id=False
        )
        cache_saved_and_served_on_consent_record(
            db,
            vendor_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.vendor_consent,
        )

        assert vendor_record.default_preference == UserConsentPreference.opt_out
        assert vendor_record.current_preference == UserConsentPreference.opt_out
        assert vendor_record.outdated_preference is None
        assert vendor_record.current_served is None
        assert vendor_record.outdated_served is None

    @pytest.mark.usefixtures(
        "privacy_preference_history_for_vendor_legitimate_interests"
    )
    def test_cache_saved_and_served_for_vendor_legitimate_interests(
        self, db, fides_user_provided_identity
    ):
        vendor_record = TCFVendorLegitimateInterestsRecord(
            id="gvl.42", name="test", description="test", has_vendor_id=True
        )
        cache_saved_and_served_on_consent_record(
            db,
            vendor_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.vendor_legitimate_interests,
        )

        assert vendor_record.default_preference == UserConsentPreference.opt_in
        assert vendor_record.current_preference == UserConsentPreference.opt_out
        assert vendor_record.outdated_preference is None
        assert vendor_record.current_served is True
        assert vendor_record.outdated_served is None

    @pytest.mark.usefixtures("privacy_preference_history_for_system")
    def test_cache_saved_and_served_for_system_consent(
        self, db, fides_user_provided_identity, system
    ):
        system_record = TCFVendorConsentRecord(id=system.id, has_vendor_id=True)
        cache_saved_and_served_on_consent_record(
            db,
            system_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.system_consent,
        )

        assert system_record.default_preference == UserConsentPreference.opt_out
        assert system_record.current_preference == UserConsentPreference.opt_in
        assert system_record.outdated_preference is None
        assert system_record.current_served is None
        assert system_record.outdated_served is None

    def test_cache_saved_and_served_for_vendor_relationships(
        self, db, fides_user_provided_identity, system
    ):
        """This is more just aggregating additional info - no consent is saved here"""
        system_record = TCFVendorRelationships(
            id=system.id, name="test", description="test", has_vendor_id=False
        )
        cache_saved_and_served_on_consent_record(
            db,
            system_record,
            fides_user_provided_identity,
            record_type=None,
        )

        assert not getattr(system_record, "default_preference", None)

    def test_cache_saved_and_served_for_tcf_special_purpose(
        self, db, fides_user_provided_identity
    ):
        sp_record = TCFSpecialPurposeRecord(
            id=2,
            name="Special Purpose 2",
            illustrations=["test illustrations"],
            data_uses=["test"],
            description="desc",
        )
        cache_saved_and_served_on_consent_record(
            db,
            sp_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.special_purpose,
        )

        assert sp_record.default_preference == UserConsentPreference.acknowledge
        assert sp_record.current_preference is None
        assert sp_record.outdated_preference is None
        assert sp_record.current_served is None
        assert sp_record.outdated_served is None

    @pytest.mark.usefixtures("privacy_preference_history_for_tcf_feature")
    def test_cache_saved_and_served_for_tcf_feature(
        self, db, fides_user_provided_identity
    ):
        feature_record = TCFFeatureRecord(
            id=2,
            name="Link different devices",
            description="Different devices can be determined as belonging to you or your household in support of one or more of purposes.",
        )
        cache_saved_and_served_on_consent_record(
            db,
            feature_record,
            fides_user_provided_identity,
            record_type=ConsentRecordType.feature,
        )

        assert feature_record.default_preference == UserConsentPreference.acknowledge
        assert feature_record.current_preference == UserConsentPreference.opt_in
        assert feature_record.outdated_preference is None
        assert feature_record.current_served is True
        assert feature_record.outdated_served is None
