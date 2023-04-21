from typing import List

import pytest
from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified

from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
    PrivacyNoticeTemplate,
)
from fides.api.ops.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.ops.schemas.privacy_notice import (
    PrivacyNoticeCreation,
    PrivacyNoticeWithId,
)
from fides.api.ops.util.consent_util import (
    add_complete_system_status_for_consent_reporting,
    add_errored_system_status_for_consent_reporting,
    cache_initial_status_and_identities_for_consent_reporting,
    create_privacy_notices_util,
    load_default_notices,
    should_opt_in_to_service,
    upsert_privacy_notice_templates_util,
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
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in

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
        privacy_declarations[0]["data_use"] = "provide.service.operations"
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
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in

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
        privacy_declarations[0]["data_use"] = "provide"
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
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in

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
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            system, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in

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
        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            None, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference == should_opt_in

    def test_conflict_preferences_opt_out_wins(
        self,
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

        collapsed_opt_in_preference, filtered_preferences = should_opt_in_to_service(
            None, privacy_request_with_consent_policy
        )
        assert collapsed_opt_in_preference is False
        assert filtered_preferences == [pref_2]

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


class TestCreatePrivacyNoticeUtils:
    def test_create_privacy_notices_util(self, db, load_default_data_uses):
        schema = PrivacyNoticeCreation(
            name="Test Notice",
            description="test description",
            internal_description="internal description",
            regions=["eu_it"],
            consent_mechanism="opt_out",
            data_uses=["train_ai_system"],
            enforcement_level=EnforcementLevel.not_applicable,
        )

        privacy_notices: List[PrivacyNotice] = create_privacy_notices_util(db, [schema])

        assert len(privacy_notices) == 1
        notice = privacy_notices[0]
        assert notice.name == "Test Notice"
        assert notice.description == "test description"
        assert notice.internal_description == "internal description"
        assert notice.regions == [PrivacyNoticeRegion.eu_it]
        assert notice.consent_mechanism == ConsentMechanism.opt_out
        assert notice.enforcement_level == EnforcementLevel.not_applicable
        assert notice.disabled is False
        assert notice.has_gpc_flag is False
        assert notice.displayed_in_privacy_center is True
        assert notice.displayed_in_overlay is True
        assert notice.displayed_in_api is True

        assert notice.privacy_notice_history_id is not None

        db.delete(notice.histories[0])
        db.delete(notice)


class TestLoadDefaultNotices:
    def test_load_default_notices(self, db, load_default_data_uses):
        # Load notice from a file that only has one template (A) defined.
        # This should create one template (A), one notice (A), and one notice history (A)
        new_templates, new_privacy_notices = load_default_notices(
            db, "tests/fixtures/test_privacy_notice.yml"
        )
        assert len(new_privacy_notices) == 1
        notice = new_privacy_notices[0]
        assert notice.name == "Test Privacy Notice"
        assert notice.description == "This website uses cookies."
        assert notice.internal_description == "This is a contrived template for testing"
        assert notice.regions == [PrivacyNoticeRegion.ca_nl]
        assert notice.consent_mechanism == ConsentMechanism.opt_in
        assert notice.enforcement_level == EnforcementLevel.system_wide
        assert notice.disabled is False
        assert notice.has_gpc_flag is True
        assert notice.displayed_in_privacy_center is False
        assert notice.displayed_in_overlay is True
        assert notice.displayed_in_api is False
        assert notice.version == 1.0

        assert notice.privacy_notice_history_id is not None
        history = notice.histories[0]
        assert history.name == "Test Privacy Notice"
        assert history.description == "This website uses cookies."
        assert (
            history.internal_description == "This is a contrived template for testing"
        )
        assert history.regions == [PrivacyNoticeRegion.ca_nl]
        assert history.consent_mechanism == ConsentMechanism.opt_in
        assert history.enforcement_level == EnforcementLevel.system_wide
        assert history.disabled is False
        assert history.has_gpc_flag is True
        assert history.displayed_in_privacy_center is False
        assert history.displayed_in_overlay is True
        assert history.displayed_in_api is False
        assert history.version == 1.0

        assert len(new_templates) == 1
        assert new_templates[0].id == notice.origin
        template_id = notice.origin
        template = db.query(PrivacyNoticeTemplate).get(template_id)
        assert template.name == "Test Privacy Notice"
        assert template.description == "This website uses cookies."
        assert (
            template.internal_description == "This is a contrived template for testing"
        )
        assert template.regions == [PrivacyNoticeRegion.ca_nl]
        assert template.consent_mechanism == ConsentMechanism.opt_in
        assert template.enforcement_level == EnforcementLevel.system_wide
        assert template.disabled is False
        assert template.has_gpc_flag is True
        assert template.displayed_in_privacy_center is False
        assert template.displayed_in_overlay is True
        assert template.displayed_in_api is False

        # Load two notices from new file.
        # One notice is an update of the previous template (A), the other is brand new (B).
        # This should update the existing template (A), create a separate new template (B),
        # and then create a new notice (B) and notice history (B) from just the new template (B).
        # Leave the existing notice (A) and notice history (A) untouched.
        new_templates, new_privacy_notices = load_default_notices(
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
        assert new_template.regions == [PrivacyNoticeRegion.ca_ns]
        assert new_template.consent_mechanism == ConsentMechanism.opt_out
        assert new_template.enforcement_level == EnforcementLevel.frontend
        assert new_template.disabled is True
        assert new_template.has_gpc_flag is False
        assert new_template.displayed_in_privacy_center is True
        assert new_template.displayed_in_overlay is False
        assert new_template.displayed_in_api is False
        assert new_template.id != template.id

        # Updated template A, consent mechanism and internal description were updated
        db.refresh(template)
        assert template.name == "Test Privacy Notice"
        assert template.description == "This website uses cookies."
        assert (
            template.internal_description
            == "This is an existing template that we are updating to make the default opt_out instead."
        )
        assert template.regions == [PrivacyNoticeRegion.ca_nl]
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
        assert new_privacy_notice.regions == [PrivacyNoticeRegion.ca_ns]
        assert new_privacy_notice.consent_mechanism == ConsentMechanism.opt_out
        assert new_privacy_notice.enforcement_level == EnforcementLevel.frontend
        assert new_privacy_notice.disabled is True
        assert new_privacy_notice.has_gpc_flag is False
        assert new_privacy_notice.displayed_in_privacy_center is True
        assert new_privacy_notice.displayed_in_overlay is False
        assert new_privacy_notice.displayed_in_api is False
        assert new_privacy_notice.version == 1.0
        assert new_privacy_notice.id != notice.id

        # Newly created privacy notice history (B)
        assert new_privacy_notice.privacy_notice_history_id is not None
        new_history = new_privacy_notice.histories[0]
        assert new_history.name == "Other Privacy Notice"
        assert new_history.description == "This website uses a large amount of cookies."
        assert (
            new_history.internal_description
            == "This is another template added for testing"
        )
        assert new_history.regions == [PrivacyNoticeRegion.ca_ns]
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
        assert notice.internal_description == "This is a contrived template for testing"
        assert notice.regions == [PrivacyNoticeRegion.ca_nl]
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
            history.internal_description == "This is a contrived template for testing"
        )
        assert history.regions == [PrivacyNoticeRegion.ca_nl]
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
            load_default_notices(
                db, "tests/fixtures/test_bad_privacy_notices_update.yml"
            )

        new_history.delete(db)
        history.delete(db)

        new_privacy_notice.delete(db)
        notice.delete(db)

        new_template.delete(db)
        template.delete(db)


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
                        regions=["eu_it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["provide"],
                        enforcement_level=EnforcementLevel.system_wide,
                    ),
                    PrivacyNoticeWithId(
                        id="test_id_1",
                        name="A",
                        regions=["eu_it"],
                        consent_mechanism=ConsentMechanism.opt_out,
                        data_uses=["provide"],
                        enforcement_level=EnforcementLevel.frontend,
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
                        name="A",
                        regions=["eu_it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["provide"],
                        enforcement_level=EnforcementLevel.system_wide,
                    ),
                    PrivacyNoticeWithId(
                        id="test_id_2",
                        name="B",
                        regions=["eu_it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["provide.service"],
                        enforcement_level=EnforcementLevel.frontend,
                        disabled=True,
                    ),
                ],
            )
        assert exc._excinfo[1].status_code == 422
        assert (
            exc._excinfo[1].detail
            == "Privacy Notice 'A' has already assigned data use 'provide' to region 'eu_it'"
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
                        regions=["eu_it"],
                        consent_mechanism=ConsentMechanism.opt_in,
                        data_uses=["bad use"],
                        enforcement_level=EnforcementLevel.system_wide,
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
                    name="A",
                    regions=["eu_it"],
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=["provide"],
                    enforcement_level=EnforcementLevel.system_wide,
                ),
                PrivacyNoticeWithId(
                    id="test_id_2",
                    name="B",
                    regions=["eu_it"],
                    consent_mechanism=ConsentMechanism.opt_in,
                    data_uses=["improve"],
                    enforcement_level=EnforcementLevel.frontend,
                    disabled=True,
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
        assert first_template.regions == [PrivacyNoticeRegion.eu_it]
        assert first_template.consent_mechanism == ConsentMechanism.opt_in
        assert first_template.data_uses == ["provide"]
        assert first_template.enforcement_level == EnforcementLevel.system_wide

        assert second_template.id == "test_id_2"
        assert second_template.name == "B"
        assert second_template.regions == [PrivacyNoticeRegion.eu_it]
        assert second_template.consent_mechanism == ConsentMechanism.opt_in
        assert second_template.data_uses == ["improve"]
        assert second_template.enforcement_level == EnforcementLevel.frontend
        assert second_template.disabled

        templates = upsert_privacy_notice_templates_util(
            db,
            [
                PrivacyNoticeWithId(
                    id="test_id_2",
                    name="B",
                    regions=["eu_it"],
                    consent_mechanism=ConsentMechanism.opt_out,
                    data_uses=["advertising"],
                    enforcement_level=EnforcementLevel.frontend,
                    disabled=True,
                ),
                PrivacyNoticeWithId(
                    id="test_id_3",
                    name="C",
                    regions=["eu_it"],
                    consent_mechanism=ConsentMechanism.opt_out,
                    data_uses=["improve"],
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
        assert first_template.regions == [PrivacyNoticeRegion.eu_it]
        assert first_template.consent_mechanism == ConsentMechanism.opt_in
        assert first_template.data_uses == ["provide"]
        assert first_template.enforcement_level == EnforcementLevel.system_wide

        # Second template updated data use and consent mechanism
        assert second_template.id == "test_id_2"
        assert second_template.name == "B"
        assert second_template.regions == [PrivacyNoticeRegion.eu_it]
        assert second_template.consent_mechanism == ConsentMechanism.opt_out
        assert second_template.data_uses == ["advertising"]
        assert second_template.enforcement_level == EnforcementLevel.frontend
        assert second_template.disabled

        # Third template is new
        assert third_template.id == "test_id_3"
        assert third_template.name == "C"
        assert third_template.regions == [PrivacyNoticeRegion.eu_it]
        assert third_template.consent_mechanism == ConsentMechanism.opt_out
        assert third_template.data_uses == ["improve"]
        assert third_template.enforcement_level == EnforcementLevel.system_wide
        assert not third_template.disabled
