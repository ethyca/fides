"""Test consent utils"""

from __future__ import annotations

from html import unescape

import pytest
from fastapi import HTTPException
from fideslang import DataUse
from pydantic import ValidationError
from sqlalchemy.orm.attributes import flag_modified
from starlette.exceptions import HTTPException

from fides.api.app_setup import (
    DEFAULT_PRIVACY_NOTICES_PATH,
    PRIVACY_EXPERIENCE_CONFIGS_PATH,
)
from fides.api.common_exceptions import ValidationError as FidesValidationError
from fides.api.models.privacy_experience import BannerEnabled, ComponentType
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    Language,
    PrivacyNoticeRegion,
    PrivacyNoticeTemplate,
)
from fides.api.models.privacy_preference_v2 import PrivacyPreferenceHistory
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.models.sql_models import DataUse as sql_DataUse
from fides.api.schemas.privacy_experience import (
    ExperienceConfigCreate,
    ExperienceConfigCreateTemplate,
)
from fides.api.schemas.privacy_notice import PrivacyNoticeCreation, PrivacyNoticeWithId
from fides.api.util.consent_util import (
    EEA_COUNTRIES,
    add_complete_system_status_for_consent_reporting,
    add_errored_system_status_for_consent_reporting,
    cache_initial_status_and_identities_for_consent_reporting,
    create_default_experience_config,
    create_default_tcf_purpose_overrides_on_startup,
    create_privacy_notices_util,
    get_fides_user_device_id_provided_identity,
    load_default_experience_configs_on_startup,
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


class TestCreatePrivacyNoticeUtils:
    @pytest.mark.usefixtures("load_default_data_uses")
    def test_create_privacy_notices_util(self, db):
        schema = PrivacyNoticeCreation(
            name="Test Notice",
            notice_key="test_notice",
            internal_description="internal description",
            consent_mechanism="opt_out",
            data_uses=["train_ai_system"],
            enforcement_level=EnforcementLevel.not_applicable,
            translations=[
                {
                    "language": Language.english,
                    "title": "A",
                    "description": "A description",
                }
            ],
        )

        privacy_notices = create_privacy_notices_util(db, [schema])

        assert len(privacy_notices) == 1
        notice = privacy_notices[0]
        assert notice.name == "Test Notice"
        assert notice.notice_key == "test_notice"
        assert notice.internal_description == "internal description"
        assert notice.consent_mechanism == ConsentMechanism.opt_out
        assert notice.enforcement_level == EnforcementLevel.not_applicable
        assert notice.disabled is False
        assert notice.has_gpc_flag is False

        translation = notice.translations[0]
        assert translation.title == "A"
        assert translation.description == "A description"
        assert translation.language == Language.english

        history = translation.histories[0]

        assert history.id == translation.privacy_notice_history_id
        assert history.name == "Test Notice"
        assert history.notice_key == "test_notice"
        assert history.internal_description == "internal description"
        assert history.consent_mechanism == ConsentMechanism.opt_out
        assert history.enforcement_level == EnforcementLevel.not_applicable
        assert history.disabled is False
        assert history.has_gpc_flag is False

        assert history.description == "A description"
        assert history.title == "A"
        assert history.language == Language.english

        db.delete(history)
        db.delete(translation)
        db.delete(notice)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_enabled_data_use_constraint(self, db):
        """Test enabled/data use logic - enabled must have data uses."""
        # default is enabled, should throw error if no data uses
        with pytest.raises(FidesValidationError):
            create_privacy_notices_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        notice_key="a",
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=[],
                        enforcement_level=EnforcementLevel.system_wide,
                        translations=[
                            {
                                "language": Language.english,
                                "title": "A",
                                "description": "A description",
                            }
                        ],
                    )
                ],
            )

        # explicitly enabled should throw error if no data uses
        with pytest.raises(FidesValidationError):
            create_privacy_notices_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        disabled=False,
                        notice_key="a",
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=[],
                        enforcement_level=EnforcementLevel.system_wide,
                    )
                ],
            )

        # if disabled, we can have no data uses
        templates = create_privacy_notices_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_1",
                    name="A",
                    disabled=True,
                    notice_key="a",
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=[],
                    enforcement_level=EnforcementLevel.system_wide,
                )
            ],
        )

        # ensure our template was created properly
        assert len(templates) == 1
        assert templates[0].id == "test_id_1"
        assert templates[0].disabled is True


class TestLoadDefaultNotices:
    @pytest.mark.usefixtures("load_default_data_uses")
    def test_load_default_notices(self, db):
        # Load notice from a file that only has one template (A) defined.
        # This should create one template (A), one notice (A), one translation (A) and one notice history (A)
        new_templates, new_privacy_notices = load_default_notices_on_startup(
            db, "tests/fixtures/test_privacy_notice.yml"
        )

        assert len(new_privacy_notices) == 1
        notice = new_privacy_notices[0]
        assert notice.name == "Test Privacy Notice"
        assert (
            unescape(notice.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert (
            notice.internal_description
            == "This is a contrived template for testing.  This field&#x27;s for internal testing!"
        )  # Stored escaped
        assert notice.consent_mechanism == ConsentMechanism.opt_in
        assert notice.enforcement_level == EnforcementLevel.system_wide
        assert notice.disabled is False
        assert notice.has_gpc_flag is True

        assert len(notice.translations) == 1
        translation = notice.translations[0]

        assert translation.title == "Test Privacy Notice"
        assert translation.description == "This is my test&#x27;s description."
        assert translation.language == Language.english

        history = translation.histories[0]

        assert history.name == "Test Privacy Notice"
        assert history.notice_key == "test_privacy_notice"
        assert history.title == "Test Privacy Notice"
        assert history.language == Language.english
        assert history.description == "This is my test&#x27;s description."
        assert (
            unescape(history.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert history.consent_mechanism == ConsentMechanism.opt_in
        assert history.enforcement_level == EnforcementLevel.system_wide
        assert history.disabled is False
        assert history.has_gpc_flag is True
        assert history.version == 1.0
        assert history.origin == new_templates[0].id

        assert len(new_templates) == 1
        assert new_templates[0].id == notice.origin
        template_id = notice.origin
        template = db.query(PrivacyNoticeTemplate).get(template_id)
        assert template.name == "Test Privacy Notice"
        assert (
            unescape(template.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert template.consent_mechanism == ConsentMechanism.opt_in
        assert template.enforcement_level == EnforcementLevel.system_wide
        assert template.disabled is False
        assert template.has_gpc_flag is True
        assert (
            template.id == "pri-5bd5cee7-8c8c-4da7-9a5c-7617a7d4dbb2"
        ), "Id hardoded in template"
        assert template.translations == [
            {
                "title": "Test Privacy Notice",
                "language": "en",
                "description": "This is my test&#x27;s description.",
            }
        ]

        # Load two notices from new file.
        # One notice is an update of the previous template (A), the other is brand new (B).
        # This should update the existing template (A), create a separate new template (B),
        # and then create a new notice (B) new translation (B) and notice history (B) from just the new template (B).
        # Leave the existing notice (A) translation (A) and notice history (A) untouched.

        new_templates, new_privacy_notices = load_default_notices_on_startup(
            db, "tests/fixtures/test_privacy_notice_update.yml"
        )
        assert len(new_templates) == 1
        # New template (B) created
        new_template = new_templates[0]
        assert new_template.name == "Other Privacy Notice"
        assert (
            new_template.internal_description
            == "This is another template added for testing"
        )
        assert new_template.consent_mechanism == ConsentMechanism.opt_out
        assert new_template.enforcement_level == EnforcementLevel.frontend
        assert new_template.disabled is True
        assert new_template.has_gpc_flag is False
        assert new_template.id != template.id
        assert new_template.id == "pri-685486d9-f532-4951-bb1a-b15fea586ff8"

        # Updated template A, consent mechanism, internal description, and translations were updated
        db.refresh(template)
        assert template.name == "Test Privacy Notice"
        assert (
            template.internal_description
            == "This is an existing template that we are updating to make the default opt_out instead."
        )
        assert template.consent_mechanism == ConsentMechanism.opt_out  # Updated value
        assert template.enforcement_level == EnforcementLevel.system_wide
        assert template.disabled is False
        assert template.has_gpc_flag is True
        assert template.translations == [
            {
                "title": "Test Privacy Notice",
                "language": "en",
                "description": "This is my updated test description!",
            }
        ]

        # Newly created privacy notice (B)
        assert len(new_privacy_notices) == 1
        new_privacy_notice = new_privacy_notices[0]
        assert new_privacy_notice.name == "Other Privacy Notice"
        assert (
            new_privacy_notice.internal_description
            == "This is another template added for testing"
        )
        assert new_privacy_notice.consent_mechanism == ConsentMechanism.opt_out
        assert new_privacy_notice.enforcement_level == EnforcementLevel.frontend
        assert new_privacy_notice.disabled is True
        assert new_privacy_notice.has_gpc_flag is False
        assert new_privacy_notice.version == 1.0
        assert new_privacy_notice.id != notice.id
        assert len(new_privacy_notice.translations) == 1
        new_translation = new_privacy_notice.translations[0]
        assert new_translation.language == Language.english
        assert new_translation.title == "Other Privacy Notice Title"
        assert new_translation.description == "Other description"

        # Newly created privacy notice history (B)
        new_history = new_translation.histories[0]
        assert new_history.name == "Other Privacy Notice"
        assert (
            new_history.internal_description
            == "This is another template added for testing"
        )
        assert new_history.consent_mechanism == ConsentMechanism.opt_out
        assert new_history.enforcement_level == EnforcementLevel.frontend
        assert new_history.disabled is True
        assert new_history.has_gpc_flag is False
        assert new_history.version == 1.0
        assert new_history.id != new_translation.id != template.id
        assert new_history.version == 1.0

        # Existing notice A - assert this wasn't updated.
        db.refresh(notice)
        assert notice.name == "Test Privacy Notice"
        assert (
            unescape(notice.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert notice.consent_mechanism == ConsentMechanism.opt_in
        assert notice.enforcement_level == EnforcementLevel.system_wide
        assert notice.disabled is False
        assert notice.has_gpc_flag is True
        assert notice.version == 1.0

        assert len(notice.translations) == 1
        translation = notice.translations[0]

        assert translation.title == "Test Privacy Notice"
        assert translation.description == "This is my test&#x27;s description."
        assert translation.language == Language.english

        assert translation.histories.count() == 1

        db.refresh(history)
        # Existing history B - assert this wasn't updated.
        assert history.name == "Test Privacy Notice"
        assert history.description == "This is my test&#x27;s description."
        assert (
            unescape(history.internal_description)
            == "This is a contrived template for testing.  This field's for internal testing!"
        )
        assert history.consent_mechanism == ConsentMechanism.opt_in
        assert history.enforcement_level == EnforcementLevel.system_wide
        assert history.disabled is False
        assert history.has_gpc_flag is True
        assert history.version == 1.0
        assert history.language == Language.english
        assert history.title == "Test Privacy Notice"
        assert history.id != new_history.id

        new_history.delete(db)
        history.delete(db)

        new_translation.delete(db)
        translation.delete(db)

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
        first_template = new_templates[0]
        assert len(first_template.translations) >= 1
        assert len(new_privacy_notices) >= 1
        pn = new_privacy_notices[0]
        assert len(pn.translations) >= 1
        translation = pn.translations[0]
        assert translation.histories.count() == 1


class TestUpsertPrivacyNoticeTemplates:
    @pytest.mark.usefixtures("load_default_data_uses")
    def test_ensure_unique_ids(self, db):
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
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["essential"],
                        enforcement_level=EnforcementLevel.system_wide,
                        translations=[
                            {
                                "language": Language.english,
                                "title": "A",
                                "description": "A description",
                            }
                        ],
                    ),
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        consent_mechanism=ConsentMechanism.opt_out,
                        data_uses=["essential"],
                        enforcement_level=EnforcementLevel.frontend,
                    ),
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert (
            exc._excinfo[1].detail
            == "More than one provided PrivacyNotice with ID test_id_1."
        )

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_bad_data_uses(self, db):
        """Test data uses must exist"""
        # explicitly enabled should throw error if no data uses
        with pytest.raises(HTTPException) as exc:
            upsert_privacy_notice_templates_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        disabled=False,
                        notice_key="a",
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=[],
                        enforcement_level=EnforcementLevel.system_wide,
                    )
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert (
            exc._excinfo[1].detail
            == "A privacy notice must have at least one data use assigned in order to be enabled."
        )

        # if disabled, we can have no data uses
        templates = upsert_privacy_notice_templates_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_1",
                    name="A",
                    disabled=True,
                    notice_key="a",
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=[],
                    enforcement_level=EnforcementLevel.system_wide,
                )
            ],
        )

        # ensure our template was created properly
        assert len(templates) == 1
        assert templates[0].id == "test_id_1"
        assert templates[0].disabled is True

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_duplicate_translations(self, db):
        """Test assert supplied translations aren't duplicated"""
        with pytest.raises(ValidationError) as exc:
            upsert_privacy_notice_templates_util(
                db,
                [
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        notice_key="a",
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["marketing"],
                        enforcement_level=EnforcementLevel.system_wide,
                        translations=[
                            {"language": Language.english, "title": "A"},
                            {"language": Language.english, "title": "B"},
                        ],
                    )
                ],
            )
        assert (
            exc._excinfo[1].errors()[0]["msg"]
            == "Multiple translations supplied for the same language"
        )

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_create_two_templates_then_update_second(self, db):
        """Test create two brand new templates"""
        templates = upsert_privacy_notice_templates_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_1",
                    notice_key="a",
                    name="A",
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=["essential"],
                    enforcement_level=EnforcementLevel.system_wide,
                    translations=[
                        {
                            "language": Language.english,
                            "title": "A",
                            "description": "A description",
                        }
                    ],
                ),
                PrivacyNoticeWithId(
                    id="test_id_2",
                    notice_key="b",
                    name="B",
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=["functional"],
                    enforcement_level=EnforcementLevel.frontend,
                    disabled=True,
                    translations=[
                        {
                            "language": Language.english,
                            "title": "B",
                            "description": "B description",
                        }
                    ],
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
        assert first_template.consent_mechanism == ConsentMechanism.opt_in
        assert first_template.data_uses == ["essential"]
        assert first_template.enforcement_level == EnforcementLevel.system_wide
        assert first_template.translations == [
            {
                "language": Language.english.value,
                "title": "A",
                "description": "A description",
            }
        ]

        assert second_template.id == "test_id_2"
        assert second_template.name == "B"
        assert second_template.consent_mechanism == ConsentMechanism.opt_in
        assert second_template.data_uses == ["functional"]
        assert second_template.enforcement_level == EnforcementLevel.frontend
        assert second_template.disabled
        assert second_template.translations == [
            {
                "language": Language.english.value,
                "title": "B",
                "description": "B description",
            }
        ]

        templates = upsert_privacy_notice_templates_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_2",
                    notice_key="b",
                    name="B",
                    consent_mechanism=ConsentMechanism.opt_out,
                    data_uses=["marketing.advertising"],
                    enforcement_level=EnforcementLevel.frontend,
                    disabled=True,
                ),
                PrivacyNoticeWithId(
                    id="test_id_3",
                    notice_key="c",
                    name="C",
                    consent_mechanism=ConsentMechanism.opt_out,
                    data_uses=["functional"],
                    enforcement_level=EnforcementLevel.system_wide,
                    disabled=False,
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
        assert first_template.consent_mechanism == ConsentMechanism.opt_in
        assert first_template.data_uses == ["essential"]
        assert first_template.enforcement_level == EnforcementLevel.system_wide

        # Second template updated data use and consent mechanism
        assert second_template.id == "test_id_2"
        assert second_template.name == "B"
        assert second_template.consent_mechanism == ConsentMechanism.opt_out
        assert second_template.data_uses == ["marketing.advertising"]
        assert second_template.enforcement_level == EnforcementLevel.frontend
        assert second_template.disabled

        # Third template is new
        assert third_template.id == "test_id_3"
        assert third_template.name == "C"
        assert third_template.consent_mechanism == ConsentMechanism.opt_out
        assert third_template.data_uses == ["functional"]
        assert third_template.enforcement_level == EnforcementLevel.system_wide
        assert not third_template.disabled


class TestLoadDefaultExperienceConfigs:
    @pytest.mark.usefixtures("load_default_data_uses")
    def test_load_default_experience_configs(self, db, privacy_notice):
        # Load notice from a file that only has one template (A) defined.
        # This should create one template (A), one experience config (A), one translation (A) and one config history (A), two experiences - one for each region (A) and link the experience notices
        new_exp_templates, new_experiences = load_default_experience_configs_on_startup(
            db, "tests/fixtures/test_privacy_experience_config.yml"
        )

        # Verify Experience Config Template
        assert len(new_exp_templates) == 1
        template = new_exp_templates[0]
        assert template.regions == [PrivacyNoticeRegion.be, PrivacyNoticeRegion.bg]
        assert template.component == ComponentType.overlay
        translations = template.translations
        assert len(translations) == 1
        translation = translations[0]

        assert translation["language"] == "en"
        assert translation["title"] == "Manage your consent preferences"
        assert translation["accept_button_label"] == "Opt in to all"

        assert len(new_experiences) == 1
        experience_config = new_experiences[0]

        # Verify Experience Config
        updated = experience_config.updated_at
        assert experience_config.origin == template.id != experience_config.id
        assert experience_config.component == ComponentType.overlay
        assert experience_config.dismissable is True
        assert experience_config.privacy_notices == [privacy_notice]

        # Verify Experiences
        assert experience_config.experiences.count() == 2
        for exp in experience_config.experiences:
            assert exp.component == ComponentType.overlay
            assert exp.experience_config_id == experience_config.id
            assert exp.region in [PrivacyNoticeRegion.be, PrivacyNoticeRegion.bg]

        # Verify Translation
        assert len(experience_config.translations) == 1
        translation = experience_config.translations[0]

        assert translation.experience_config_id == experience_config.id
        assert translation.language == Language.english
        assert translation.title == "Manage your consent preferences"
        assert translation.description.startswith(
            "We use your organization&#x27;s cookies and similar methods"
        )
        assert translation.is_default
        assert translation.privacy_policy_link_label == "Privacy Policy"

        # Assert Translation History
        assert translation.histories.count() == 1
        history = translation.histories[0]

        assert history.dismissable
        assert history.origin == template.id
        assert history.language == Language.english
        assert history.title == "Manage your consent preferences"
        assert history.description.startswith(
            "We use your organization&#x27;s cookies and similar methods"
        )
        assert history.is_default
        assert history.privacy_policy_link_label == "Privacy Policy"
        assert history.translation_id == translation.id
        assert history.version == 1.0

        # Update templates - templates should change but existing configs should not
        (
            updated_exp_templates,
            updated_configs,
        ) = load_default_experience_configs_on_startup(
            db, "tests/fixtures/test_privacy_experience_config_update.yml"
        )

        assert len(updated_exp_templates) == 1
        assert len(updated_configs) == 0

        assert len(updated_exp_templates) == 1
        updated_template = updated_exp_templates[0]
        assert updated_template.regions == [
            PrivacyNoticeRegion.be,
            PrivacyNoticeRegion.bg,
            PrivacyNoticeRegion.us_ca,
        ]
        assert updated_template.id == template.id
        assert template.component == ComponentType.overlay
        updated_template_translations = template.translations
        assert len(updated_template_translations) == 1
        temp_translation = updated_template_translations[0]
        assert temp_translation["language"] == "en"
        assert temp_translation["title"] == "Manage your consent preferences"
        assert temp_translation["accept_button_label"] == "Opt in!"

        db.refresh(experience_config)
        db.refresh(translation)
        db.refresh(history)
        assert experience_config.updated_at == updated
        assert len(experience_config.translations) == 1
        assert translation.accept_button_label == "Opt in to all"
        assert len(experience_config.privacy_notices) == 1
        assert history.version == 1.0
        assert len(experience_config.regions) == 2

        history.delete(db)
        translation.delete(db)
        experience_config.delete(db)
        template.delete(db)

    def test_load_actual_default_experiences(self, db):
        """Sanity check, makings sure that default experiences don't load with errors"""
        (
            new_templates,
            new_experience_configs,
        ) = load_default_experience_configs_on_startup(
            db, PRIVACY_EXPERIENCE_CONFIGS_PATH
        )
        assert len(new_templates) >= 1
        assert len(new_experience_configs) >= 1
        exp_config = new_experience_configs[0]
        assert len(exp_config.translations) >= 1
        assert len(exp_config.regions) >= 1
        assert exp_config.origin is not None
        assert len(exp_config.translations) >= 1
        translation = exp_config.translations[0]

        assert translation.histories.count() == 1

        tcf_config = next(
            config
            for config in new_experience_configs
            if config.component == ComponentType.tcf_overlay
        )
        experiences_created = tcf_config.experiences
        assert experiences_created.count() == len(EEA_COUNTRIES)
        be_exp = experiences_created[0]
        assert be_exp.component == ComponentType.tcf_overlay
        assert be_exp.region == PrivacyNoticeRegion.be

        assert len(tcf_config.translations) >= 1

        translation = tcf_config.translations[0]
        assert translation.histories.count() == 1


class TestUpsertDefaultExperienceConfig:
    @pytest.fixture(scope="function")
    def default_overlay_config_data(self, db, privacy_notice):
        return ExperienceConfigCreate(
            **{
                "component": ComponentType.overlay,
                "id": "test_id",
                "regions": [PrivacyNoticeRegion.us_ca],
                "privacy_notice_ids": [privacy_notice.id],
                "translations": [
                    {
                        "language": "en",
                        "accept_button_label": "A",
                        "acknowledge_button_label": "B",
                        "banner_description": "J",
                        "banner_title": "K",
                        "description": "C",
                        "privacy_preferences_link_label": "D",
                        "privacy_policy_link_label": "E's label",
                        "privacy_policy_url": "https://example.com/privacy_policy",
                        "reject_button_label": "G",
                        "save_button_label": "H",
                        "title": "I",
                        "is_default": True,
                    }
                ],
            }
        )

    def test_create_default_experience_config(
        self, db, default_overlay_config_data, privacy_notice
    ):
        experience_config = create_default_experience_config(
            db, default_overlay_config_data
        )
        assert experience_config.component == ComponentType.overlay
        assert experience_config.regions == [PrivacyNoticeRegion.us_ca]
        assert experience_config.privacy_notices == [privacy_notice]
        translation = experience_config.translations[0]

        assert translation.accept_button_label == "A"
        assert translation.acknowledge_button_label == "B"
        assert translation.created_at is not None
        assert translation.description == "C"
        assert translation.is_default is True
        assert translation.privacy_preferences_link_label == "D"
        assert translation.privacy_policy_link_label == "E&#x27;s label"  # Escaped
        assert translation.privacy_policy_url == "https://example.com/privacy_policy"
        assert translation.reject_button_label == "G"
        assert translation.save_button_label == "H"
        assert translation.title == "I"
        assert translation.updated_at is not None

        # Asserting history created appropriately
        assert translation.histories.count() == 1
        history = translation.histories[0]
        assert history.translation_id == translation.id

        assert history.accept_button_label == "A"
        assert history.acknowledge_button_label == "B"
        assert history.component == ComponentType.overlay
        assert history.created_at is not None
        assert history.description == "C"
        assert history.is_default is True
        assert history.id != "test_id"
        assert history.privacy_preferences_link_label == "D"
        assert history.privacy_policy_link_label == "E&#x27;s label"
        assert history.privacy_policy_url == "https://example.com/privacy_policy"
        assert history.reject_button_label == "G"
        assert history.save_button_label == "H"
        assert history.title == "I"
        assert history.updated_at is not None
        assert history.version == 1.0
        assert history.language == Language.english

        db.delete(translation)
        db.delete(history)
        db.delete(experience_config)

    def test_create_duplicate_experience_translations(
        self, db, default_overlay_config_data
    ):
        with pytest.raises(ValidationError) as exc:
            config = ExperienceConfigCreateTemplate(
                **{
                    "component": ComponentType.overlay,
                    "id": "test_id",
                    "privacy_notice_keys": ["example_privacy_notice"],
                    "translations": [
                        {
                            "language": "en",
                            "accept_button_label": "A",
                            "banner_description": "J",
                            "banner_title": "K",
                            "description": "C",
                            "acknowledge_button_label": "B",
                            "privacy_preferences_link_label": "D",
                            "privacy_policy_link_label": "E's label",
                            "privacy_policy_url": "https://example.com/privacy_policy",
                            "reject_button_label": "G",
                            "save_button_label": "H",
                            "title": "I",
                            "is_default": True,
                        },
                        {
                            "language": "en",
                            "accept_button_label": "A",
                            "banner_description": "J",
                            "banner_title": "K",
                            "description": "C",
                            "acknowledge_button_label": "B",
                            "privacy_preferences_link_label": "D",
                            "privacy_policy_link_label": "E's label",
                            "privacy_policy_url": "https://example.com/privacy_policy",
                            "reject_button_label": "G",
                            "save_button_label": "H",
                            "title": "I",
                            "is_default": True,
                        },
                    ],
                }
            )
            create_default_experience_config(db, config)

        assert (
            str(exc.value.args[0][0].exc)
            == "Multiple translations supplied for the same language"
        )


class TestValidateDataUses:
    @pytest.fixture(scope="function")
    def privacy_notice_request(self):
        return PrivacyNoticeCreation(
            name="sample privacy notice",
            notice_key="sample_privacy_notice",
            consent_mechanism=ConsentMechanism.opt_in,
            data_uses=["placeholder"],
            enforcement_level=EnforcementLevel.system_wide,
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
