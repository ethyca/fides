import pytest

from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.util.tcf.tcf_experience_contents import get_tcf_base_query_and_filters


class TestMatchingPrivacyDeclarations:
    """Tests matching privacy declarations returned that are the basis of the TCF Experience and the "relevant_systems"
    that are saved for consent reporting
    """

    @pytest.mark.usefixtures(
        "emerse_system",
    )
    def test_get_matching_privacy_declarations_enable_purpose_override_is_false(
        self, db
    ):
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

    @pytest.mark.usefixtures("emerse_system", "enable_override_vendor_purposes")
    def test_privacy_declaration_publisher_overrides(
        self,
        db,
    ):
        """Define some purpose legal basis overrides and check their effects on what is returned in the Privacy Declaration query"""

        # Defined legal basis is also Consent for purpose 1 on Emerse.
        # Publisher override matches.
        TCFPurposeOverride.create(
            db,
            data={"purpose": 1, "is_included": True, "required_legal_basis": "Consent"},
        )

        # Defined legal basis is Legitimate Interests for purpose 2 on Emerse.
        # Here, Purpose 2 is specified to be excluded.
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 2,
                "is_included": False,
            },
        )

        # Defined legal basis is Consent for purpose 3 on Emerse.
        # No legal basis override is defined.
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 3,
                "is_included": True,
                "required_legal_basis": None,
            },
        )

        # Defined legal basis is Consent for purpose 4 on Emerse.
        # Override here has a different legal basis
        TCFPurposeOverride.create(
            db,
            data={
                "purpose": 4,
                "is_included": True,
                "required_legal_basis": "Legitimate interests",
            },
        )

        declarations, _, _ = get_tcf_base_query_and_filters(db)

        legal_basis_overrides = {
            declaration.purpose: declaration.legal_basis_for_processing
            for declaration in declarations
            if declaration.purpose
        }

        # Purpose 2 has been removed altogether and Purpose 4 Legal Basis
        # has been overridden to Legitimate Interests legal basis
        assert legal_basis_overrides == {
            9: "Legitimate interests",
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
            9: "Legitimate interests",
            8: "Legitimate interests",
            7: "Legitimate interests",
            4: "Consent",
            3: "Consent",
            1: "Consent",
        }

        # The three declarations on Emerse with data uses mapping to Purpose 2 have been excluded
        assert declarations.count() == 10
