import pytest

from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.util.tcf.tcf_experience_contents import get_tcf_base_query_and_filters


class TestBaseTCFQuery:
    """Tests matching privacy declarations returned that are the basis of the TCF Experience and the "relevant_systems"
    that are saved for consent reporting
    """

    @pytest.mark.usefixtures(
        "emerse_system",
    )
    def test_get_matching_privacy_declarations_enable_purpose_override_is_false(
        self, db
    ):
        """No legal bases are overridden because this features is off"""
        declarations, _, _ = get_tcf_base_query_and_filters(db)

        assert declarations.count() == 13

        mapping = {
            declaration.data_use: declaration.purpose for declaration in declarations
        }

        # marketing.advertising.serving, essential.service.security, essential.fraud_detection map to special purposes, not purposes
        assert mapping == {
            "marketing.advertising.serving": None,
            "essential.service.security": None,
            "essential.fraud_detection": None,
            "analytics.reporting.campaign_insights": 9,
            "analytics.reporting.content_performance": 8,
            "analytics.reporting.ad_performance": 7,
            "marketing.advertising.frequency_capping": 2,
            "marketing.advertising.first_party.contextual": 2,
            "marketing.advertising.negative_targeting": 2,
            "marketing.advertising.first_party.targeted": 4,
            "marketing.advertising.third_party.targeted": 4,
            "marketing.advertising.profiling": 3,
            "functional.storage": 1,
        }

    @pytest.mark.parametrize(
        "override_fixture",
        [
            "enable_override_vendor_purposes",
            "enable_override_vendor_purposes_api_set",  # ensure override functionality works when config is set via API
        ],
    )
    def test_privacy_declaration_purpose_overrides(
        self, override_fixture, request, db, emerse_system
    ):
        """Comprehensive test of the various scenarios for privacy declaration purpose overrides when building the
        base TCF query

        Some of the specifics aren't configurations that would be allowed for emerse, but ignore that here.
        """
        request.getfixturevalue(override_fixture)
        # As some test setup, override purpose 7 declaration to have an inflexible legal basis
        purpose_7_decl = next(
            decl
            for decl in emerse_system.privacy_declarations
            if decl.data_use == "analytics.reporting.ad_performance"
        )
        purpose_7_decl.flexible_legal_basis_for_processing = False
        purpose_7_decl.save(db)

        # and override purpose 9 declaration to have an inflexible legal basis -
        # we'll ensure this can be overriden for exclusion even with inflexible legal basis

        purpose_9_decl = next(
            decl
            for decl in emerse_system.privacy_declarations
            if decl.data_use == "analytics.reporting.campaign_insights"
        )
        purpose_9_decl.flexible_legal_basis_for_processing = False
        purpose_9_decl.save(db)

        # For more test setup, create some purpose overrides

        # Purpose override that matches the legal basis already on the system's declaration
        TCFPurposeOverride.create(
            db,
            data={"purpose": 1, "is_included": True, "required_legal_basis": "Consent"},
        )

        # Purpose override that marks Purpose 2 as excluded
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 2,
                "is_included": False,
            },
        )

        # Purpose override object defined, but no legal basis override specified
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 3,
                "is_included": True,
                "required_legal_basis": None,
            },
        )

        # Purpose override defined with different legal basis than the one on the System's declaration
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 4,
                "is_included": True,
                "required_legal_basis": "Legitimate interests",
            },
        )

        # Purpose override defined with differing legal basis, however, purpose 7 above was marked as inflexible
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 7,
                "is_included": True,
                "required_legal_basis": "Consent",
            },
        )

        # Purpose override to mark purpose 9 as excluded. purpose 9 has been marked as inflexible legal basis.
        # we ensure that it's still excluded even with an inflexible legal basis.
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 9,
                "is_included": False,
            },
        )

        declarations, _, _ = get_tcf_base_query_and_filters(db)

        legal_basis_overrides = {
            declaration.purpose: declaration.legal_basis_for_processing
            for declaration in declarations
            if declaration.purpose
        }

        # Purpose 1 had no change, because the override matched
        # Purpose 2 has been removed altogether
        # Purpose 4 Legal Basis has been overridden to Legitimate Interests legal basis
        # Purpose 7's override wasn't applied because that declaration was marked as inflexible.
        # Purpose 9 has been removed altogether - even with an inflexible legal basis
        assert legal_basis_overrides == {
            8: "Legitimate interests",
            7: "Legitimate interests",
            4: "Legitimate interests",
            3: "Consent",
            1: "Consent",
        }

        original_legal_basis = {
            declaration.purpose: declaration.original_legal_basis_for_processing
            for declaration in declarations
            if declaration.purpose
        }
        assert original_legal_basis == {
            8: "Legitimate interests",
            7: "Legitimate interests",
            4: "Consent",
            3: "Consent",
            1: "Consent",
        }

        # The 4 declarations on Emerse with data uses mapping to Purposes 2 and 9 have been excluded
        assert declarations.count() == 9
