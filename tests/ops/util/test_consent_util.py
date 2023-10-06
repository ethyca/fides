from __future__ import annotations

from html import unescape

import pytest
from fastapi import HTTPException
from fideslang import DataUse
from sqlalchemy.orm.attributes import flag_modified
from starlette.exceptions import HTTPException

from fides.api.app_setup import DEFAULT_PRIVACY_NOTICES_PATH
from fides.api.models.privacy_experience import (
    BannerEnabled,
    ComponentType,
    PrivacyExperience,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNoticeRegion,
    PrivacyNoticeTemplate,
)
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.sql_models import DataUse as sql_DataUse
from fides.api.schemas.privacy_notice import PrivacyNoticeCreation, PrivacyNoticeWithId
from fides.api.util.consent_util import (
    EEA_COUNTRIES,
    add_complete_system_status_for_consent_reporting,
    add_errored_system_status_for_consent_reporting,
    cache_initial_status_and_identities_for_consent_reporting,
    create_default_experience_config,
    create_privacy_notices_util,
    create_tcf_experiences_on_startup,
    get_fides_user_device_id_provided_identity,
    load_default_notices_on_startup,
    should_opt_in_to_service,
    upsert_privacy_notice_templates_util,
    validate_notice_data_uses,
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
        Privacy Notice Data Use = "marketing.advertising"
        System Data Use = "marketing.advertising"
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
        privacy_notice_fr_provide_service_frontend_only,
        fides_user_provided_identity,
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
                "privacy_notice_history_id": privacy_notice_fr_provide_service_frontend_only.privacy_notice_history_id,
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
        Privacy Notice Data Use = "essential.service.operations"
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
        Privacy Notice Data Use = "marketing.advertising" but not checked w/ no system
        other Privacy Notice Data Use = "essential" but not checked w/ no system
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


class TestCreatePrivacyNoticeUtils:
    def test_create_privacy_notices_util(self, db, load_default_data_uses):
        schema = PrivacyNoticeCreation(
            name="Test Notice",
            notice_key="test_notice",
            description="test description",
            internal_description="internal description",
            regions=["it"],
            consent_mechanism="opt_out",
            data_uses=["train_ai_system"],
            enforcement_level=EnforcementLevel.not_applicable,
            displayed_in_privacy_center=True,
        )

        privacy_notices, affected_regions = create_privacy_notices_util(db, [schema])
        assert affected_regions == {PrivacyNoticeRegion.it}

        assert len(privacy_notices) == 1
        notice = privacy_notices[0]
        assert notice.name == "Test Notice"
        assert notice.notice_key == "test_notice"
        assert notice.description == "test description"
        assert notice.internal_description == "internal description"
        assert notice.regions == [PrivacyNoticeRegion.it]
        assert notice.consent_mechanism == ConsentMechanism.opt_out
        assert notice.enforcement_level == EnforcementLevel.not_applicable
        assert notice.disabled is False
        assert notice.has_gpc_flag is False
        assert notice.displayed_in_privacy_center is True
        assert notice.displayed_in_overlay is False
        assert notice.displayed_in_api is False

        assert notice.privacy_notice_history_id is not None
        history = notice.histories[0]
        assert history.id == notice.privacy_notice_history_id
        assert history.name == "Test Notice"
        assert history.notice_key == "test_notice"
        assert history.description == "test description"
        assert history.internal_description == "internal description"
        assert history.regions == [PrivacyNoticeRegion.it]
        assert history.consent_mechanism == ConsentMechanism.opt_out
        assert history.enforcement_level == EnforcementLevel.not_applicable
        assert history.disabled is False
        assert history.has_gpc_flag is False
        assert history.displayed_in_privacy_center is True
        assert history.displayed_in_overlay is False
        assert history.displayed_in_api is False

        db.delete(notice.histories[0])
        db.delete(notice)


class TestLoadDefaultNotices:
    def test_load_default_notices(self, db, load_default_data_uses):
        # Load notice from a file that only has one template (A) defined.
        # This should create one template (A), one notice (A), and one notice history (A)
        (
            overlay_exp,
            privacy_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )
        assert overlay_exp is None
        assert privacy_exp is None

        new_templates, new_privacy_notices = load_default_notices_on_startup(
            db, "tests/fixtures/test_privacy_notice.yml"
        )
        assert len(new_privacy_notices) == 1
        notice = new_privacy_notices[0]
        assert notice.name == "Test Privacy Notice"
        assert notice.notice_key == "test_privacy_notice"
        assert notice.description == "This website uses cookies."
        assert (
            unescape(notice.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert (
            notice.internal_description
            == "This is a contrived template for testing.  This field&#x27;s for internal testing!"
        )  # Stored escaped
        assert notice.regions == [PrivacyNoticeRegion.us_ak]
        assert notice.consent_mechanism == ConsentMechanism.opt_in
        assert notice.enforcement_level == EnforcementLevel.system_wide
        assert notice.disabled is False
        assert notice.has_gpc_flag is True
        assert notice.displayed_in_privacy_center is False
        assert notice.displayed_in_overlay is True
        assert notice.displayed_in_api is False
        assert notice.version == 1.0
        (
            overlay_exp,
            privacy_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_ak
        )
        assert overlay_exp is not None
        assert privacy_exp is None

        assert notice.privacy_notice_history_id is not None
        history = notice.histories[0]
        assert history.name == "Test Privacy Notice"
        assert history.notice_key == "test_privacy_notice"
        assert history.description == "This website uses cookies."
        assert (
            unescape(history.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert history.regions == [PrivacyNoticeRegion.us_ak]
        assert history.consent_mechanism == ConsentMechanism.opt_in
        assert history.enforcement_level == EnforcementLevel.system_wide
        assert history.disabled is False
        assert history.has_gpc_flag is True
        assert history.displayed_in_privacy_center is False
        assert history.displayed_in_overlay is True
        assert history.displayed_in_api is False
        assert history.version == 1.0
        assert history.origin == new_templates[0].id

        assert len(new_templates) == 1
        assert new_templates[0].id == notice.origin
        template_id = notice.origin
        template = db.query(PrivacyNoticeTemplate).get(template_id)
        assert template.name == "Test Privacy Notice"
        assert template.description == "This website uses cookies."
        assert (
            unescape(template.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert template.regions == [PrivacyNoticeRegion.us_ak]
        assert template.consent_mechanism == ConsentMechanism.opt_in
        assert template.enforcement_level == EnforcementLevel.system_wide
        assert template.disabled is False
        assert template.has_gpc_flag is True
        assert template.displayed_in_privacy_center is False
        assert template.displayed_in_overlay is True
        assert template.displayed_in_api is False
        assert (
            template.id == "pri-5bd5cee7-8c8c-4da7-9a5c-7617a7d4dbb2"
        ), "Id hardoded in template"

        # Load two notices from new file.
        # One notice is an update of the previous template (A), the other is brand new (B).
        # This should update the existing template (A), create a separate new template (B),
        # and then create a new notice (B) and notice history (B) from just the new template (B).
        # Leave the existing notice (A) and notice history (A) untouched.
        (
            overlay_exp,
            privacy_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_al
        )
        assert overlay_exp is None
        assert privacy_exp is None

        new_templates, new_privacy_notices = load_default_notices_on_startup(
            db, "tests/fixtures/test_privacy_notice_update.yml"
        )
        assert len(new_templates) == 1
        # New template (B) created
        new_template = new_templates[0]
        assert new_template.name == "Other Privacy Notice"
        assert (
            new_template.description == "This website uses a large amount of cookies."
        )
        assert (
            new_template.internal_description
            == "This is another template added for testing"
        )
        assert new_template.regions == [PrivacyNoticeRegion.us_al]
        assert new_template.consent_mechanism == ConsentMechanism.opt_out
        assert new_template.enforcement_level == EnforcementLevel.frontend
        assert new_template.disabled is True
        assert new_template.has_gpc_flag is False
        assert new_template.displayed_in_privacy_center is True
        assert new_template.displayed_in_overlay is False
        assert new_template.displayed_in_api is False
        assert new_template.id != template.id
        assert new_template.id == "pri-685486d9-f532-4951-bb1a-b15fea586ff8"

        # Updated template A, consent mechanism and internal description were updated
        db.refresh(template)
        assert template.name == "Test Privacy Notice"
        assert template.description == "This website uses cookies."
        assert (
            template.internal_description
            == "This is an existing template that we are updating to make the default opt_out instead."
        )
        assert template.regions == [PrivacyNoticeRegion.us_ak]
        assert template.consent_mechanism == ConsentMechanism.opt_out  # Updated value
        assert template.enforcement_level == EnforcementLevel.system_wide
        assert template.disabled is False
        assert template.has_gpc_flag is True
        assert template.displayed_in_privacy_center is False
        assert template.displayed_in_overlay is True
        assert template.displayed_in_api is False

        # Newly created privacy notice (B)
        assert len(new_privacy_notices) == 1
        new_privacy_notice = new_privacy_notices[0]
        assert new_privacy_notice.name == "Other Privacy Notice"
        assert (
            new_privacy_notice.description
            == "This website uses a large amount of cookies."
        )
        assert (
            new_privacy_notice.internal_description
            == "This is another template added for testing"
        )
        assert new_privacy_notice.regions == [PrivacyNoticeRegion.us_al]
        assert new_privacy_notice.consent_mechanism == ConsentMechanism.opt_out
        assert new_privacy_notice.enforcement_level == EnforcementLevel.frontend
        assert new_privacy_notice.disabled is True
        assert new_privacy_notice.has_gpc_flag is False
        assert new_privacy_notice.displayed_in_privacy_center is True
        assert new_privacy_notice.displayed_in_overlay is False
        assert new_privacy_notice.displayed_in_api is False
        assert new_privacy_notice.version == 1.0
        assert new_privacy_notice.id != notice.id

        (
            overlay_exp,
            privacy_exp,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db, PrivacyNoticeRegion.us_al
        )
        assert overlay_exp is None
        assert privacy_exp is not None

        # Newly created privacy notice history (B)
        assert new_privacy_notice.privacy_notice_history_id is not None
        new_history = new_privacy_notice.histories[0]
        assert new_history.name == "Other Privacy Notice"
        assert new_history.description == "This website uses a large amount of cookies."
        assert (
            new_history.internal_description
            == "This is another template added for testing"
        )
        assert new_history.regions == [PrivacyNoticeRegion.us_al]
        assert new_history.consent_mechanism == ConsentMechanism.opt_out
        assert new_history.enforcement_level == EnforcementLevel.frontend
        assert new_history.disabled is True
        assert new_history.has_gpc_flag is False
        assert new_history.displayed_in_privacy_center is True
        assert new_history.displayed_in_overlay is False
        assert new_history.displayed_in_api is False
        assert new_history.version == 1.0
        assert new_history.id != notice.id
        assert new_history.version == 1.0

        # Existing notice A - assert this wasn't updated.
        db.refresh(notice)
        assert notice.name == "Test Privacy Notice"
        assert notice.description == "This website uses cookies."
        assert (
            unescape(notice.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert notice.regions == [PrivacyNoticeRegion.us_ak]
        assert notice.consent_mechanism == ConsentMechanism.opt_in
        assert notice.enforcement_level == EnforcementLevel.system_wide
        assert notice.disabled is False
        assert notice.has_gpc_flag is True
        assert notice.displayed_in_privacy_center is False
        assert notice.displayed_in_overlay is True
        assert notice.displayed_in_api is False
        assert notice.version == 1.0
        assert notice.histories.count() == 1

        db.refresh(history)
        # Existing history B - assert this wasn't updated.
        assert history.name == "Test Privacy Notice"
        assert history.description == "This website uses cookies."
        assert (
            unescape(history.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert history.regions == [PrivacyNoticeRegion.us_ak]
        assert history.consent_mechanism == ConsentMechanism.opt_in
        assert history.enforcement_level == EnforcementLevel.system_wide
        assert history.disabled is False
        assert history.has_gpc_flag is True
        assert history.displayed_in_privacy_center is False
        assert history.displayed_in_overlay is True
        assert history.displayed_in_api is False
        assert history.version == 1.0
        assert history.id != new_history.id

        with pytest.raises(HTTPException):
            load_default_notices_on_startup(
                db, "tests/fixtures/test_bad_privacy_notices_update.yml"
            )

        new_history.delete(db)
        history.delete(db)

        new_privacy_notice.delete(db)
        notice.delete(db)

        new_template.delete(db)
        template.delete(db)

    def test_load_actual_default_notices(self, db):
        """Sanity check, makings sure that default privacy notices don't load with errors"""
        new_templates, new_privacy_notices = load_default_notices_on_startup(
            db, DEFAULT_PRIVACY_NOTICES_PATH
        )
        assert len(new_templates) >= 1
        assert len(new_privacy_notices) >= 1


class TestUpsertPrivacyNoticeTemplates:
    def test_ensure_unique_ids(self, db, load_default_data_uses):
        """Can help make sure we don't actually try to upload templates with duplicate
        ids due to copy/pasting
        """
        with pytest.raises(HTTPException) as exc:
            upsert_privacy_notice_templates_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["essential"],
                        enforcement_level=EnforcementLevel.system_wide,
                        displayed_in_overlay=True,
                    ),
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_out,
                        data_uses=["essential"],
                        enforcement_level=EnforcementLevel.frontend,
                        displayed_in_overlay=True,
                    ),
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert (
            exc._excinfo[1].detail
            == "More than one provided PrivacyNotice with ID test_id_1."
        )

    def test_overlapping_data_uses(self, db, load_default_data_uses):
        """Can't have overlaps on incoming templates, and we also check these for disabled templates"""
        with pytest.raises(HTTPException) as exc:
            upsert_privacy_notice_templates_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        notice_key="a",
                        name="A",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["essential"],
                        enforcement_level=EnforcementLevel.system_wide,
                        displayed_in_overlay=True,
                    ),
                    PrivacyNoticeWithId(
                        id="test_id_2",
                        notice_key="b",
                        name="B",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["essential.service"],
                        enforcement_level=EnforcementLevel.frontend,
                        disabled=True,
                        displayed_in_overlay=True,
                    ),
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert (
            exc._excinfo[1].detail
            == "Privacy Notice 'A' has already assigned data use 'essential' to region 'it'"
        )

    def test_overlapping_notice_keys(self, db, load_default_data_uses):
        """Can't have overlapping notice keys on incoming templates, and we also check these for disabled templates"""
        with pytest.raises(HTTPException) as exc:
            upsert_privacy_notice_templates_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        notice_key="a",
                        name="A",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["essential"],
                        enforcement_level=EnforcementLevel.system_wide,
                        displayed_in_overlay=True,
                    ),
                    PrivacyNoticeWithId(
                        id="test_id_2",
                        notice_key="a",
                        name="B",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["marketing"],
                        enforcement_level=EnforcementLevel.frontend,
                        disabled=True,
                        displayed_in_overlay=True,
                    ),
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert (
            exc._excinfo[1].detail
            == "Privacy Notice 'A' has already assigned notice key 'a' to region 'it'"
        )

    def test_bad_data_uses(self, db, load_default_data_uses):
        """Test data uses must exist"""
        with pytest.raises(HTTPException) as exc:
            upsert_privacy_notice_templates_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        notice_key="a",
                        regions=["it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["bad use"],
                        enforcement_level=EnforcementLevel.system_wide,
                        displayed_in_overlay=True,
                    )
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert exc._excinfo[1].detail == "Unknown data_use 'bad use'"

    def test_create_two_templates_then_update_second(self, db, load_default_data_uses):
        """Test create two brand new templates"""
        templates = upsert_privacy_notice_templates_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_1",
                    notice_key="a",
                    name="A",
                    regions=["it"],
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=["essential"],
                    enforcement_level=EnforcementLevel.system_wide,
                    displayed_in_overlay=True,
                ),
                PrivacyNoticeWithId(
                    id="test_id_2",
                    notice_key="b",
                    name="B",
                    regions=["it"],
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=["functional"],
                    enforcement_level=EnforcementLevel.frontend,
                    disabled=True,
                    displayed_in_overlay=True,
                ),
            ],
        )
        assert len(templates) == 2
        first_template = templates[0]
        first_template_updated_at = first_template.updated_at
        second_template = templates[1]
        second_template_updated_at = second_template.updated_at

        assert first_template.id == "test_id_1"
        assert first_template.name == "A"
        assert first_template.regions == [PrivacyNoticeRegion.it]
        assert first_template.consent_mechanism == ConsentMechanism.opt_in
        assert first_template.data_uses == ["essential"]
        assert first_template.enforcement_level == EnforcementLevel.system_wide

        assert second_template.id == "test_id_2"
        assert second_template.name == "B"
        assert second_template.regions == [PrivacyNoticeRegion.it]
        assert second_template.consent_mechanism == ConsentMechanism.opt_in
        assert second_template.data_uses == ["functional"]
        assert second_template.enforcement_level == EnforcementLevel.frontend
        assert second_template.disabled

        templates = upsert_privacy_notice_templates_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_2",
                    notice_key="b",
                    name="B",
                    regions=["it"],
                    consent_mechanism=ConsentMechanism.opt_out,
                    data_uses=["marketing.advertising"],
                    enforcement_level=EnforcementLevel.frontend,
                    disabled=True,
                    displayed_in_overlay=True,
                ),
                PrivacyNoticeWithId(
                    id="test_id_3",
                    notice_key="c",
                    name="C",
                    regions=["it"],
                    consent_mechanism=ConsentMechanism.opt_out,
                    data_uses=["functional"],
                    enforcement_level=EnforcementLevel.system_wide,
                    disabled=False,
                    displayed_in_overlay=True,
                ),
            ],
        )

        second_template_updated = templates[0]
        third_template = templates[1]

        db.refresh(first_template)
        db.refresh(second_template)
        assert first_template.updated_at == first_template_updated_at
        assert second_template.updated_at > second_template_updated_at
        assert second_template_updated.id == second_template.id

        # First template didn't change
        assert first_template.id == "test_id_1"
        assert first_template.name == "A"
        assert first_template.regions == [PrivacyNoticeRegion.it]
        assert first_template.consent_mechanism == ConsentMechanism.opt_in
        assert first_template.data_uses == ["essential"]
        assert first_template.enforcement_level == EnforcementLevel.system_wide

        # Second template updated data use and consent mechanism
        assert second_template.id == "test_id_2"
        assert second_template.name == "B"
        assert second_template.regions == [PrivacyNoticeRegion.it]
        assert second_template.consent_mechanism == ConsentMechanism.opt_out
        assert second_template.data_uses == ["marketing.advertising"]
        assert second_template.enforcement_level == EnforcementLevel.frontend
        assert second_template.disabled

        # Third template is new
        assert third_template.id == "test_id_3"
        assert third_template.name == "C"
        assert third_template.regions == [PrivacyNoticeRegion.it]
        assert third_template.consent_mechanism == ConsentMechanism.opt_out
        assert third_template.data_uses == ["functional"]
        assert third_template.enforcement_level == EnforcementLevel.system_wide
        assert not third_template.disabled


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
            "privacy_policy_link_label": "E's label",
            "privacy_policy_url": "F",
            "reject_button_label": "G",
            "save_button_label": "H",
            "title": "I",
        }

    def test_create_default_experience_config(self, db, default_overlay_config_data):
        experience_config = create_default_experience_config(
            db, default_overlay_config_data
        )

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
        assert (
            experience_config.privacy_policy_link_label == "E&#x27;s label"
        )  # Escaped
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
        assert history.privacy_policy_link_label == "E&#x27;s label"
        assert history.privacy_policy_url == "F"
        assert history.reject_button_label == "G"
        assert history.save_button_label == "H"
        assert history.title == "I"
        assert history.updated_at is not None
        assert history.version == 1.0

        db.delete(history)
        db.delete(experience_config)

    def test_create_default_experience_config_config_already_exists_no_change(
        self, db, default_overlay_config_data
    ):
        """Experience config is not changed in any way"""
        experience_config = create_default_experience_config(
            db, default_overlay_config_data
        )
        assert experience_config is not None

        resp = create_default_experience_config(db, default_overlay_config_data)
        assert resp is None

        db.refresh(experience_config)

        # Nothing changed so we don't want to update the version
        assert experience_config.version == 1.0
        assert experience_config.histories.count() == 1

        db.delete(experience_config.histories[0])
        db.delete(experience_config)

    def test_default_experience_config_data_has_changed(
        self, db, default_overlay_config_data
    ):
        """Even though data has changed, we don't update existing experience config"""
        experience_config = create_default_experience_config(
            db, default_overlay_config_data
        )
        assert experience_config is not None

        default_overlay_config_data["privacy_policy_url"] = "example.com/privacy_policy"

        resp = create_default_experience_config(db, default_overlay_config_data)
        assert resp is None

        db.refresh(experience_config)

        # Data has changed but we didn't update existing config
        assert experience_config.version == 1.0
        assert experience_config.privacy_policy_url != "example.com/privacy_policy"
        assert experience_config.histories.count() == 1

        assert experience_config.experience_config_history_id is not None
        assert experience_config.experience_config_history_id != "test_id"
        history = experience_config.histories[0]

        assert history.version == 1.0
        assert experience_config.privacy_policy_url != "example.com/privacy_policy"

        history.delete(db)
        experience_config.delete(db)

    def test_trying_to_use_this_function_to_create_non_default_configs(
        self, db, default_overlay_config_data
    ):
        default_overlay_config_data["is_default"] = False

        with pytest.raises(Exception):
            create_default_experience_config(db, default_overlay_config_data)

    def test_create_default_experience_config_validation_error(
        self, db, default_overlay_config_data
    ):
        default_overlay_config_data[
            "banner_enabled"
        ] = None  # Marking required field as None

        with pytest.raises(ValueError) as exc:
            create_default_experience_config(db, default_overlay_config_data)

        assert (
            str(exc.value.args[0][0].exc)
            == "The following additional fields are required when defining an overlay: acknowledge_button_label, banner_enabled, and privacy_preferences_link_label."
        )


class TestValidateDataUses:
    @pytest.fixture(scope="function")
    def privacy_notice_request(self):
        return PrivacyNoticeCreation(
            name="sample privacy notice",
            notice_key="sample_privacy_notice",
            regions=[PrivacyNoticeRegion.us_ca],
            consent_mechanism=ConsentMechanism.opt_in,
            data_uses=["placeholder"],
            enforcement_level=EnforcementLevel.system_wide,
            displayed_in_overlay=True,
        )

    @pytest.fixture(scope="function")
    def custom_data_use(self, db):
        return sql_DataUse.create(
            db=db,
            data=DataUse(
                fides_key="new_data_use",
                organization_fides_key="default_organization",
                name="New data use",
                description="A test data use",
                parent_key=None,
            ).dict(),
        )

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_invalid(
        self, db, privacy_notice_request: PrivacyNoticeCreation
    ):
        privacy_notice_request.data_uses = ["invalid_data_use"]
        with pytest.raises(HTTPException):
            validate_notice_data_uses([privacy_notice_request], db)

        privacy_notice_request.data_uses = ["marketing.advertising", "invalid_data_use"]
        with pytest.raises(HTTPException):
            validate_notice_data_uses([privacy_notice_request], db)

        privacy_notice_request.data_uses = [
            "marketing.advertising",
            "marketing.advertising.invalid_data_use",
        ]
        with pytest.raises(HTTPException):
            validate_notice_data_uses([privacy_notice_request], db)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_default_taxonomy(
        self, db, privacy_notice_request: PrivacyNoticeCreation
    ):
        privacy_notice_request.data_uses = ["marketing.advertising"]
        validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["marketing.advertising", "essential"]
        validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = [
            "marketing.advertising",
            "essential",
            "essential.service",
        ]
        validate_notice_data_uses([privacy_notice_request], db)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_custom_uses(
        self,
        db,
        privacy_notice_request: PrivacyNoticeCreation,
        custom_data_use: sql_DataUse,
    ):
        """
        Ensure custom data uses added to the DB are considered valid
        """

        privacy_notice_request.data_uses = [custom_data_use.fides_key]
        validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = [
            "marketing.advertising",
            custom_data_use.fides_key,
        ]
        validate_notice_data_uses([privacy_notice_request], db)


class TestLoadTCFExperiences:
    def test_create_tcf_experiences_on_startup(self, db):
        """Sanity check on creating TCF experiences"""
        experiences_created = create_tcf_experiences_on_startup(db)
        assert len(experiences_created) == len(EEA_COUNTRIES)
        be_exp = experiences_created[0]
        assert be_exp.component == ComponentType.tcf_overlay
        assert be_exp.region == PrivacyNoticeRegion.be
        experience_config = be_exp.experience_config
        assert experience_config.is_default
        assert experience_config.component == ComponentType.tcf_overlay
