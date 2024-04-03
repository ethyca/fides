"""Test consent utils"""

from __future__ import annotations

import pytest
from sqlalchemy.orm.attributes import flag_modified

from fides.api.models.privacy_preference_v2 import PrivacyPreferenceHistory
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.util.consent_util import (
    add_complete_system_status_for_consent_reporting,
    add_errored_system_status_for_consent_reporting,
    cache_initial_status_and_identities_for_consent_reporting,
    create_default_tcf_purpose_overrides_on_startup,
    get_fides_user_device_id_provided_identity,
    should_opt_in_to_service,
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
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "marketing.advertising"
        System Data Use = "marketing.advertising"
        """
        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
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
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "essential"
        System Data Use = "essential.service.operations"
        """
        privacy_declarations = system.privacy_declarations
        system.privacy_declarations[0].update(
            db=db, data={"data_use": "essential.service.operations"}
        )

        system.privacy_declarations = privacy_declarations
        flag_modified(system, "privacy_declarations")
        system.save(db)

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_ca_provide.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
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
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "essential.service.operations"
        System Data Use = "essential"
        """
        privacy_declarations = system.privacy_declarations
        system.privacy_declarations[0].update(db=db, data={"data_use": "essential"})
        system.privacy_declarations = privacy_declarations
        flag_modified(system, "privacy_declarations")
        system.save(db)

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_co_provide_service_operations.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
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
        privacy_notice_fr_provide_service_frontend_only,
    ):
        """
        Privacy Notice Enforcement Level = "frontend"
        Privacy Notice Data Use = "essential.service" but not checked
        System Data Use = "marketing.advertising"
        """
        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_fr_provide_service_frontend_only.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
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
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "essential.service.operations"
        """

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_co_provide_service_operations.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
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
    ):
        """
        Privacy Notice Enforcement Level = "system_wide"
        Privacy Notice Data Use = "marketing.advertising" but not checked w/ no system
        other Privacy Notice Data Use = "essential" but not checked w/ no system
        """
        pref_1 = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
            },
            check_name=False,
        )
        pref_2 = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_out",
                "privacy_notice_history_id": privacy_notice_us_ca_provide.translations[
                    0
                ].privacy_notice_history_id,
                "fides_user_device": "165ad0ed-10fb-4a60-9810-e0749346ec16",
                "hashed_fides_user_device": ProvidedIdentity.hash_value(
                    "165ad0ed-10fb-4a60-9810-e0749346ec16"
                ),
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
            {"data_use": "marketing.advertising", "opt_in": False}
        ]
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is False
        assert filtered_preferences == []

        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "marketing.advertising", "opt_in": True}
        ]
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is True
        assert filtered_preferences == []

        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "marketing.advertising", "opt_in": True},
            {"data_use": "functional", "opt_in": False},
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
        privacy_preference_history_fr_provide_service_frontend_only,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        privacy_preference_history_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            connection_config,
            relevant_preferences=[
                privacy_preference_history_fr_provide_service_frontend_only
            ],
            relevant_user_identities={"email": "customer-1@example.com"},
        )

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_fr_provide_service_frontend_only)

        # Relevant systems
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.affected_system_status
            == {connection_config.name: "pending"}
        )
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.secondary_user_ids
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
        privacy_preference_history_fr_provide_service_frontend_only,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        privacy_preference_history_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            connection_config,
            relevant_preferences=[
                privacy_preference_history_fr_provide_service_frontend_only
            ],
            relevant_user_identities={"email": "customer-1@example.com"},
        )

        add_complete_system_status_for_consent_reporting(
            db, privacy_request_with_consent_policy, connection_config
        )

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_fr_provide_service_frontend_only)

        # Relevant systems
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.affected_system_status
            == {connection_config.name: "complete"}
        )
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.secondary_user_ids
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
        privacy_preference_history_fr_provide_service_frontend_only,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        privacy_preference_history_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            connection_config,
            relevant_preferences=[
                privacy_preference_history_fr_provide_service_frontend_only
            ],
            relevant_user_identities={"email": "customer-1@example.com"},
        )

        add_errored_system_status_for_consent_reporting(
            db, privacy_request_with_consent_policy, connection_config
        )

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_fr_provide_service_frontend_only)

        # Relevant systems
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.affected_system_status
            == {connection_config.name: "error"}
        )
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.secondary_user_ids
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


class TestLoadTCFPurposeOverrides:
    def test_load_tcf_purpose_overrides_on_startup(self, db):
        """Sanity check on creating TCF purpose overrides"""
        default_override_objects_added = (
            create_default_tcf_purpose_overrides_on_startup(db)
        )
        assert len(default_override_objects_added) == 11
        for override in default_override_objects_added:
            assert override.is_included is True
            assert override.required_legal_basis is None
