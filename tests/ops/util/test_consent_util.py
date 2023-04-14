import pytest
from sqlalchemy.orm.attributes import flag_modified

from fides.api.ops.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.ops.util.consent_util import should_opt_in_to_service


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
        Privacy Notice Data Use = "advertising"
        System Data Use = "advertising"
        """
        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice.privacy_notice_history_id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is should_opt_in
        )

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
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is should_opt_in
        )

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
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is should_opt_in
        )

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
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is should_opt_in
        )

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
        Privacy Notice Data Use = "provide.service.operations"
        """

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": preference,
                "privacy_notice_history_id": privacy_notice_us_co_provide_service_operations.privacy_notice_history_id,
            },
            check_name=False,
        )
        pref.privacy_request_id = privacy_request_with_consent_policy.id
        pref.save(db)
        assert (
            should_opt_in_to_service(None, privacy_request_with_consent_policy)
            is should_opt_in
        )

    @pytest.mark.parametrize(
        "preference, should_opt_in",
        [("opt_in", True), ("opt_out", False), ("acknowledge", None)],
    )
    def test_conflict_preferences_opt_out_wins(
        self,
        preference,
        should_opt_in,
        db,
        privacy_request_with_consent_policy,
        privacy_notice,
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
            },
            check_name=False,
        )
        pref_2 = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_out",
                "privacy_notice_history_id": privacy_notice.privacy_notice_history_id,
            },
            check_name=False,
        )
        pref_1.privacy_request_id = privacy_request_with_consent_policy.id
        pref_1.save(db)
        pref_2.privacy_request_id = privacy_request_with_consent_policy.id
        pref_2.save(db)

        assert (
            should_opt_in_to_service(None, privacy_request_with_consent_policy) is False
        )

    def test_old_workflow_preferences_saved_with_respect_to_data_use(
        self,
        db,
        system,
        privacy_request_with_consent_policy,
    ):
        """
        Test old workflow where executable preferences were cached on PrivacyRequest.consent_preferences
        """
        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "advertising", "opt_in": False}
        ]
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is False
        )

        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "advertising", "opt_in": True}
        ]
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is True
        )

        privacy_request_with_consent_policy.consent_preferences = [
            {"data_use": "advertising", "opt_in": True},
            {"data_use": "improve", "opt_in": False},
        ]
        assert (
            should_opt_in_to_service(system, privacy_request_with_consent_policy)
            is False
        )
