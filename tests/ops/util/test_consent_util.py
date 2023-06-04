import pytest
from sqlalchemy.orm.attributes import flag_modified

from fides.api.models.privacy_experience import BannerEnabled, ComponentType
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.util.consent_util import (
    add_complete_system_status_for_consent_reporting,
    add_errored_system_status_for_consent_reporting,
    cache_initial_status_and_identities_for_consent_reporting,
    get_fides_user_device_id_provided_identity,
    should_opt_in_to_service,
    upsert_default_experience_config,
)


class TestShouldOptIntoService:
    @pytest.mark.parametrize(
        "preference, should_opt_in",
        [("opt_in", True), ("opt_out", False), ("acknowledge", None)],
    )
    def test_matching_data_use(
        self,
        preference,
        should_opt_in,
        db,
        system,
        privacy_request_with_consent_policy,
        privacy_notice,
        fides_user_provided_identity,
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "advertising"
        System Data Use = "advertising"
        """
        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in

        pref.delete(db)

    @pytest.mark.parametrize(
        "preference, should_opt_in",
        [("opt_in", True), ("opt_out", False), ("acknowledge", None)],
    )
    def test_notice_use_is_parent_of_system_use(
        self,
        preference,
        should_opt_in,
        db,
        system,
        privacy_notice_us_ca_provide,
        privacy_request_with_consent_policy,
        fides_user_provided_identity,
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "provide"
        System Data Use = "provide.service.operations"
        """
        privacy_declarations = system.privacy_declarations
        system.privacy_declarations[0].update(
            db=db, data={"data_use": "provide.service.operations"}
        )

        system.privacy_declarations = privacy_declarations
        flag_modified(system, "privacy_declarations")
        system.save(db)

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_ca_provide.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in
        pref.delete(db)

    @pytest.mark.parametrize(
        "preference, should_opt_in",
        [("opt_in", None), ("opt_out", None), ("acknowledge", None)],
    )
    def test_notice_use_is_child_of_system_use(
        self,
        preference,
        should_opt_in,
        db,
        system,
        privacy_notice_us_co_provide_service_operations,
        privacy_request_with_consent_policy,
        fides_user_provided_identity,
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "provide.service.operations"
        System Data Use = "provide"
        """
        privacy_declarations = system.privacy_declarations
        system.privacy_declarations[0].update(db=db, data={"data_use": "provide"})
        system.privacy_declarations = privacy_declarations
        flag_modified(system, "privacy_declarations")
        system.save(db)

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_co_provide_service_operations.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in
        pref.delete(db)

    @pytest.mark.parametrize(
        "preference, should_opt_in",
        [("opt_in", None), ("opt_out", None), ("acknowledge", None)],
    )
    def test_enforcement_frontend_only(
        self,
        preference,
        should_opt_in,
        db,
        system,
        privacy_request_with_consent_policy,
        privacy_notice_eu_fr_provide_service_frontend_only,
        fides_user_provided_identity,
    ):
        """
        Privacy Notice Enforcement Level = "frontend"
        Privacy Notice Data Use = "provided.service" but not checked
        System Data Use = "advertising"
        """
        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_eu_fr_provide_service_frontend_only.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in
        pref.delete(db)

    @pytest.mark.parametrize(
        "preference, should_opt_in",
        [("opt_in", True), ("opt_out", False), ("acknowledge", None)],
    )
    def test_no_system_means_no_data_use_check(
        self,
        preference,
        should_opt_in,
        db,
        privacy_notice_us_co_provide_service_operations,
        privacy_request_with_consent_policy,
        fides_user_provided_identity,
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "provide.service.operations"
        """

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_co_provide_service_operations.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            None, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in
        pref.delete(db)

    def test_conflict_preferences_opt_out_wins(
        self,
        db,
        privacy_request_with_consent_policy,
        privacy_notice,
        privacy_notice_us_ca_provide,
        fides_user_provided_identity,
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "advertising" but not checked w/ no system
        other Privacy Notice Data Use = "provide" but not checked w/ no system
        """
        pref_1 = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref_2 = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_out",
                "privacy_notice_history_id": privacy_notice_us_ca_provide.privacy_notice_history_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
            },
            check_name=False,
        )
        pref_1.privacy_request_id = privacy_request_with_consent_policy.id
        pref_1.save(db)
        pref_2.privacy_request_id = privacy_request_with_consent_policy.id
        pref_2.save(db)

        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            None, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is False
        assert filtered_preferences == [pref_2]
        pref_1.delete(db)
        pref_2.delete(db)

    def test_old_workflow_preferences_saved_with_respect_to_data_use(
        self,
        system,
        privacy_request_with_consent_policy,
    ):
        """
        Test old workflow where executable preferences were cached on PrivacyRequest.consent_preferences
        """
        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "advertising", "opt_in": False}
        ]
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is False
        assert filtered_preferences == []

        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "advertising", "opt_in": True}
        ]
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is True
        assert filtered_preferences == []

        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "advertising", "opt_in": True},
            {"data_use": "improve", "opt_in": False},
        ]
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is False
        assert filtered_preferences == []


class TestCacheSystemStatusesForConsentReporting:
    def test_cache_initial_status_and_identities_for_consent_reporting(
        self,
        db,
        privacy_request_with_consent_policy,
        connection_config,
        privacy_preference_history,
        privacy_preference_history_eu_fr_provide_service_frontend_only,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        privacy_preference_history_eu_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            connection_config,
            relevant_preferences=[
                privacy_preference_history_eu_fr_provide_service_frontend_only
            ],
            relevant_user_identities={"email": "customer-1@example.com"},
        )

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_eu_fr_provide_service_frontend_only)

        # Relevant systems
        assert (
            privacy_preference_history_eu_fr_provide_service_frontend_only.affected_system_status
            == {connection_config.name: "pending"}
        )
        assert (
            privacy_preference_history_eu_fr_provide_service_frontend_only.secondary_user_ids
            == {"email": "customer-1@example.com"}
        )

        # non-relevant systems
        assert privacy_preference_history.affected_system_status == {
            connection_config.name: "skipped"
        }
        assert privacy_preference_history.secondary_user_ids is None

    def test_add_complete_system_status_for_consent_reporting(
        self,
        db,
        privacy_request_with_consent_policy,
        connection_config,
        privacy_preference_history,
        privacy_preference_history_eu_fr_provide_service_frontend_only,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        privacy_preference_history_eu_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            connection_config,
            relevant_preferences=[
                privacy_preference_history_eu_fr_provide_service_frontend_only
            ],
            relevant_user_identities={"email": "customer-1@example.com"},
        )

        add_complete_system_status_for_consent_reporting(
            db, privacy_request_with_consent_policy, connection_config
        )

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_eu_fr_provide_service_frontend_only)

        # Relevant systems
        assert (
            privacy_preference_history_eu_fr_provide_service_frontend_only.affected_system_status
            == {connection_config.name: "complete"}
        )
        assert (
            privacy_preference_history_eu_fr_provide_service_frontend_only.secondary_user_ids
            == {"email": "customer-1@example.com"}
        )

        # non-relevant systems
        assert privacy_preference_history.affected_system_status == {
            connection_config.name: "skipped"
        }
        assert privacy_preference_history.secondary_user_ids is None

    def test_add_error_system_status_for_consent_reporting(
        self,
        db,
        privacy_request_with_consent_policy,
        connection_config,
        privacy_preference_history,
        privacy_preference_history_eu_fr_provide_service_frontend_only,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        privacy_preference_history_eu_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            connection_config,
            relevant_preferences=[
                privacy_preference_history_eu_fr_provide_service_frontend_only
            ],
            relevant_user_identities={"email": "customer-1@example.com"},
        )

        add_errored_system_status_for_consent_reporting(
            db, privacy_request_with_consent_policy, connection_config
        )

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_eu_fr_provide_service_frontend_only)

        # Relevant systems
        assert (
            privacy_preference_history_eu_fr_provide_service_frontend_only.affected_system_status
            == {connection_config.name: "error"}
        )
        assert (
            privacy_preference_history_eu_fr_provide_service_frontend_only.secondary_user_ids
            == {"email": "customer-1@example.com"}
        )

        # non-relevant systems
        assert privacy_preference_history.affected_system_status == {
            connection_config.name: "skipped"
        }
        assert privacy_preference_history.secondary_user_ids is None


class TestGetFidesUserProvidedIdentity:
    def test_no_identifier_supplied(self, db):
        provided_identity = get_fides_user_device_id_provided_identity(db, None)
        assert provided_identity is None

    def test_no_provided_identifier_exists(self, db):
        provided_identity = get_fides_user_device_id_provided_identity(
            db, "fides_user_device_id"
        )
        assert provided_identity is None

    def test_get_fides_user_device_id_provided_identity(
        self, db, fides_user_provided_identity
    ):
        provided_identity = get_fides_user_device_id_provided_identity(
            db, "051b219f-20e4-45df-82f7-5eb68a00889f"
        )
        assert provided_identity == fides_user_provided_identity


class TestUpsertDefaultExperienceConfig:
    @pytest.fixture(scope="function")
    def default_overlay_config_data(self, db):
        return {
            "accept_button_label": "A",
            "acknowledge_button_label": "B",
            "banner_enabled": BannerEnabled.enabled_where_required,
            "component": ComponentType.overlay,
            "description": "C",
            "disabled": False,
            "is_default": True,
            "id": "test_id",
            "privacy_preferences_link_label": "D",
            "privacy_policy_link_label": "E",
            "privacy_policy_url": "F",
            "reject_button_label": "G",
            "save_button_label": "H",
            "title": "I",
        }

    def test_create_default_experience_config(self, db, default_overlay_config_data):
        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert created

        assert experience_config.accept_button_label == "A"
        assert experience_config.acknowledge_button_label == "B"
        assert experience_config.banner_enabled == BannerEnabled.enabled_where_required
        assert experience_config.component == ComponentType.overlay
        assert experience_config.created_at is not None
        assert experience_config.description == "C"
        assert not experience_config.disabled
        assert experience_config.is_default is True
        assert experience_config.id == "test_id"
        assert experience_config.privacy_preferences_link_label == "D"
        assert experience_config.privacy_policy_link_label == "E"
        assert experience_config.privacy_policy_url == "F"
        assert experience_config.regions == []
        assert experience_config.reject_button_label == "G"
        assert experience_config.save_button_label == "H"
        assert experience_config.title == "I"
        assert experience_config.updated_at is not None
        assert experience_config.version == 1.0

        # Asserting history created appropriately
        assert experience_config.experience_config_history_id is not None
        assert experience_config.experience_config_history_id != "test_id"
        assert experience_config.histories.count() == 1
        history = experience_config.histories[0]

        assert history.accept_button_label == "A"
        assert history.acknowledge_button_label == "B"
        assert history.banner_enabled == BannerEnabled.enabled_where_required
        assert history.component == ComponentType.overlay
        assert history.created_at is not None
        assert history.description == "C"
        assert not history.disabled
        assert history.experience_config_id == experience_config.id
        assert history.is_default is True
        assert history.id != "test_id"
        assert history.privacy_preferences_link_label == "D"
        assert history.privacy_policy_link_label == "E"
        assert history.privacy_policy_url == "F"
        assert history.reject_button_label == "G"
        assert history.save_button_label == "H"
        assert history.title == "I"
        assert history.updated_at is not None
        assert history.version == 1.0

        db.delete(history)
        db.delete(experience_config)

    def test_update_default_experience_config_no_change(
        self, db, default_overlay_config_data
    ):
        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert created

        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert not created

        # Nothing changed so we don't want to update the version
        assert experience_config.version == 1.0
        assert experience_config.histories.count() == 1

        db.delete(experience_config.histories[0])
        db.delete(experience_config)

    def test_update_default_experience_config(self, db, default_overlay_config_data):
        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert created

        default_overlay_config_data["privacy_policy_url"] = "example.com/privacy_policy"

        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert not created

        # Data has changed so we want to update the version
        assert experience_config.version == 2.0
        assert experience_config.privacy_policy_url == "example.com/privacy_policy"
        assert experience_config.histories.count() == 2

        assert experience_config.experience_config_history_id is not None
        assert experience_config.experience_config_history_id != "test_id"
        history = experience_config.histories[1]

        assert history.version == 2.0
        assert experience_config.privacy_policy_url == "example.com/privacy_policy"

        old_history = experience_config.histories[0]
        assert old_history.version == 1.0
        assert old_history.privacy_policy_url == "F"

        old_history.delete(db)
        history.delete(db)
        experience_config.delete(db)

    def test_trying_to_use_this_function_to_create_non_default_configs(
        self, db, default_overlay_config_data
    ):
        default_overlay_config_data["is_default"] = False

        with pytest.raises(Exception):
            upsert_default_experience_config(db, default_overlay_config_data)

    def test_create_default_experience_config_validation_error(
        self, db, default_overlay_config_data
    ):
        default_overlay_config_data[
            "banner_enabled"
        ] = None  # Marking required field as None

        with pytest.raises(ValueError) as exc:
            upsert_default_experience_config(db, default_overlay_config_data)

        assert (
            str(exc.value.args[0][0].exc)
            == "The following additional fields are required when defining an overlay: acknowledge_button_label, banner_enabled, and privacy_preferences_link_label."
        )

    def test_update_default_experience_config_validation_error(
        self, db, default_overlay_config_data
    ):
        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert created

        default_overlay_config_data["privacy_policy_url"] = "example.com/privacy_policy"

        created, experience_config = upsert_default_experience_config(
            db, default_overlay_config_data
        )
        assert not created

        default_overlay_config_data[
            "banner_enabled"
        ] = None  # Marking required field as None

        with pytest.raises(ValueError) as exc:
            upsert_default_experience_config(db, default_overlay_config_data)

        assert (
            str(exc.value.args[0][0].exc)
            == "The following additional fields are required when defining an overlay: acknowledge_button_label, banner_enabled, and privacy_preferences_link_label."
        )
